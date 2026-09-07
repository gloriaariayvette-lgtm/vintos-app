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

    def energy_of(bits):
        return fold_energy(bits, sequence, charges, hp, cw, tw)[0]

    def expected(theta):
        counts = _sample(ansatz(theta, nq, layers), nq, loop_shots)
        total = sum(counts.values()) or 1
        return sum(energy_of(raw[::-1]) * c for raw, c in counts.items()) / total

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

    folds = []
    for raw, prob in sorted(run["probabilities"].items(),
                            key=lambda kv: kv[1], reverse=True)[:60]:
        bits = raw[::-1]
        e, coords, contacts, overlaps, turns = fold_energy(bits, sequence, charges, hp, cw, tw)
        folds.append({"state": raw, "probability": round(prob, 6), "energy": round(e, 4),
                      "overlaps": overlaps, "turns": turns,
                      "contacts": [c["kind"] for c in contacts],
                      "coords": coords, "bits": bits})
    valid = [f for f in folds if f["overlaps"] == 0]
    ranked = sorted(valid or folds, key=lambda f: (f["energy"], -f["probability"]))
    best = ranked[0]
    likeliest = folds[0]

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
        "search": {"start_energy": round(float(start_energy), 4),
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
                      for f in folds[:8]],
        "distribution": run,
        "display": ["A CHAIN LOOKS FOR ITS SHAPE", "",
                    f"sequence {sequence}   charges {''.join('+' if c>0 else ('-' if c<0 else '0') for c in charges)}",
                    f"pulls  hydrophobic {hp}   charge {cw}   stiffness {tw}",
                    f"search {round(float(start_energy),3)} -> {round(float(result.fun),3)}"
                    f"   on {nq} qubits", ""] + picture + ["",
                    f"lowest energy found {best['energy']}  "
                    f"({len(best['contacts'])} contacts, {best['turns']} turns)",
                    f"the machine's favourite state was {likeliest['state']} "
                    f"at {round(likeliest['probability']*100,2)}%"],
    }
