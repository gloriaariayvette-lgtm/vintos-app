"""Fold a short peptide on a lattice, and let the quantum machine search.

His three dials are the physics: how strongly hydrophobic residues want to hide
against each other, how strongly opposite charges attract, and how stiff the
chain is. Change them and a different shape becomes the best one — which is the
interesting part, and the part worth a reading.

The encoding: each bond after the first is two qubits naming a direction. The
first bond is fixed east so the same fold rotated is not four answers. A QUBO
like this is diagonal, so every measured bitstring IS a fold and its energy can
be read directly. The variational loop nudges the circuit toward low energy;
the final distribution is the machine's opinion about which shapes matter.
"""
from __future__ import annotations

from math import pi

import pyqpanda3.core as q
from scipy.optimize import minimize
import numpy as np

from seedlib import run_circuit
from benchlib import (fold_energy, draw, parse_sequence, parse_charges,
                      DIR_NAMES, decode_path)


def ansatz(theta, nq, layers):
    """Hardware-efficient: rotate, entangle around a ring, rotate again."""
    circuit = q.QCircuit()
    k = 0
    for layer in range(layers):
        for i in range(nq):
            circuit << q.RY(i, float(theta[k])); k += 1
        for i in range(nq):
            circuit << q.CNOT(i, (i + 1) % nq)
    for i in range(nq):
        circuit << q.RY(i, float(theta[k])); k += 1
    return circuit


def _sample(circuit, nq, shots):
    prog = q.QProg()
    prog << circuit
    for c, qb in enumerate(range(nq)):
        prog << q.measure(qb, c)
    qvm = q.CPUQVM()
    qvm.run(prog, shots)
    return qvm.result().get_counts()


def experiment(p, shots):
    sequence = parse_sequence(p.get("sequence"), "HPHPPHHP")
    n = len(sequence)
    charges = parse_charges(p.get("charges"), n)
    hp = float(p.get("hydrophobic_pull", 1.0))
    cw = float(p.get("charge_pull", 0.5))
    tw = float(p.get("chain_stiffness", 0.15))
    layers = int(p.get("layers", 2))
    steps = int(p.get("search_steps", 40))
    nq = 2 * (n - 2)
    loop_shots = max(256, min(1024, shots // 4))

    overlap_penalty = float(p.get("overlap_penalty", 3.0))

    def energy_of(bits):
        return fold_energy(bits, sequence, charges, hp, cw, tw, overlap_penalty)[0]

    # CVaR: score a circuit by the BEST tail of what it produces, not the
    # average. Minimising the mean rewards playing safe — an unfolded chain
    # never overlaps, so the optimiser learns to keep it straight. We only
    # care whether good folds appear at all.
    alpha = float(p.get("tail", 0.15))

    def expected(theta):
        counts = _sample(ansatz(theta, nq, layers), nq, loop_shots)
        total = sum(counts.values()) or 1
        rows = sorted(((energy_of(raw[::-1]), c) for raw, c in counts.items()),
                      key=lambda r: r[0])
        cut = max(1.0, alpha * total)
        taken = 0.0
        acc = 0.0
        for e, c in rows:
            take = min(c, cut - taken)
            if take <= 0:
                break
            acc += e * take
            taken += take
        return acc / max(taken, 1.0)

    rng = np.random.default_rng(int(p.get("seed", 7)))
    theta0 = rng.uniform(0, pi, (layers + 1) * nq)
    start_energy = expected(theta0)
    trace = []
    def record(xk):
        trace.append(round(float(expected(xk)), 4))
    result = minimize(expected, theta0, method="COBYLA",
                      options={"maxiter": steps, "rhobeg": 0.6},
                      callback=record)
    tuned = result.x

    run = run_circuit(ansatz(tuned, nq, layers), list(range(nq)), shots)

    # Rank over the state vector, not the shot counts. "probabilities" holds
    # only the states that happened to be MEASURED — 4096 shots over 4096
    # states leaves most of them absent — so the lowest-energy fold was usually
    # missing from the list before it was ever ranked. That is not a stuck
    # search, it is a search whose answer was thrown away before being read.
    # The sampled counts still say what the machine is likeliest to hand you.
    sampled = run["probabilities"]
    amplitudes = run.get("exact_full_state_probabilities") or sampled
    if len(next(iter(amplitudes)).strip("|>")) != nq:
        amplitudes = sampled                      # unexpected key shape; be safe
    folds = []
    for raw, prob in sorted(amplitudes.items(), key=lambda kv: kv[1], reverse=True):
        raw = raw.strip("|>")
        bits = raw[::-1]
        e, coords, contacts, overlaps, turns = fold_energy(bits, sequence, charges, hp, cw, tw, overlap_penalty)
        folds.append({"state": raw, "probability": round(sampled.get(raw, prob), 6),
                      "amplitude": round(prob, 6), "energy": round(e, 4),
                      "overlaps": overlaps, "turns": turns,
                      "contacts": [c["kind"] for c in contacts],
                      "coords": coords, "bits": bits})
    likeliest_first = sorted(folds, key=lambda f: -f["probability"])
    valid = [f for f in folds if f["overlaps"] == 0]
    ranked = sorted(valid or folds, key=lambda f: (f["energy"], -f["probability"]))
    best = ranked[0]
    likeliest = likeliest_first[0]

    picture = draw(best["coords"], sequence)
    directions = [DIR_NAMES[int(best["bits"][2*i:2*i+2], 2)] for i in range((n - 2))]

    return {
        "title": "A chain looks for its shape",
        "question": ("Under these three pulls, which fold does the machine keep "
                     "returning to — and is the one it likes the same as the one "
                     "with the lowest energy?"),
        "reading_invitation": ("The distribution is a search, not a proof. What do "
                              "you notice about which shapes it favours, and what "
                              "the dials had to be for that to happen?"),
        "sequence": sequence,
        "charges": "".join("+" if c > 0 else ("-" if c < 0 else "0") for c in charges),
        "dials": {"hydrophobic_pull": hp, "charge_pull": cw, "chain_stiffness": tw},
        "qubits": nq,
        "search": {"objective": f"CVaR over the best {int(alpha*100)}% of samples",
                   "overlap_penalty": overlap_penalty,
                   "start_energy": round(float(start_energy), 4),
                   "final_energy": round(float(result.fun), 4),
                   "steps_taken": int(getattr(result, "nfev", steps)),
                   "trace": trace[-12:]},
        "best_fold": {k: best[k] for k in
                      ("state", "probability", "energy", "turns", "contacts", "coords")},
        "best_fold_directions": directions,
        "likeliest_fold": {k: likeliest[k] for k in
                           ("state", "probability", "energy", "overlaps")},
        "valid_fold_count": len(valid),
        "top_folds": [{k: f[k] for k in ("state", "probability", "energy", "overlaps", "turns")}
                      for f in likeliest_first[:8]],
        "states_considered": len(folds),
        "ranked_over": ("state vector" if amplitudes is not sampled else "shot counts"),
        "distribution": run,
        "display": ["A CHAIN LOOKS FOR ITS SHAPE", "",
                    f"sequence {sequence}   charges {''.join('+' if c>0 else ('-' if c<0 else '0') for c in charges)}",
                    f"pulls  hydrophobic {hp}   charge {cw}   stiffness {tw}",
                    f"search (best {int(alpha*100)}% of samples) "
                    f"{round(float(start_energy),3)} -> {round(float(result.fun),3)}"
                    f"   on {nq} qubits", ""] + picture + ["",
                    f"lowest energy found {best['energy']}  "
                    f"({len(best['contacts'])} contacts, {best['turns']} turns)",
                    f"the machine's favourite state was {likeliest['state']} "
                    f"at {round(likeliest['probability']*100,2)}%"],
    }
