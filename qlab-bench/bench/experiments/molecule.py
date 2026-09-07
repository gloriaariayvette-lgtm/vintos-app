"""Find a molecule's ground state, and check the answer against the truth.

This is the real thing rather than a toy: PySCF computes the molecular
integrals, OpenFermion maps them onto qubits, and the quantum machine searches
for the lowest energy. Because the molecules are small we can also compute the
exact answer classically, so every run is gradeable — the machine either found
it or it did not, and by how much.

His dial here is the bond length. Pull the atoms apart and watch the energy
climb out of the well; that curve is what a chemical bond actually is.
"""
from __future__ import annotations

from math import pi

import numpy as np
import pyqpanda3.core as q
from scipy.optimize import minimize

HARTREE_TO_KCAL = 627.5094740631

MOLECULES = {
    "H2":   {"atoms": ["H", "H"], "default_length": 0.735, "charge": 0, "multiplicity": 1,
             "note": "two hydrogens; the simplest bond there is"},
    "HeH+": {"atoms": ["He", "H"], "default_length": 0.772, "charge": 1, "multiplicity": 1,
             "note": "the first molecule the universe ever made"},
    "LiH":  {"atoms": ["Li", "H"], "default_length": 1.595, "charge": 0, "multiplicity": 1,
             "note": "ionic; the electrons sit lopsided"},
}


def _hamiltonian(name, length, active=None):
    from openfermion.chem import MolecularData
    from openfermionpyscf import run_pyscf
    from openfermion.transforms import get_fermion_operator, jordan_wigner
    spec = MOLECULES[name]
    geometry = [(spec["atoms"][0], (0.0, 0.0, 0.0)),
                (spec["atoms"][1], (0.0, 0.0, float(length)))]
    mol = MolecularData(geometry, "sto-3g", spec["multiplicity"], spec["charge"])
    mol = run_pyscf(mol, run_scf=True, run_fci=True)
    if active:
        occupied, act = active
        mh = mol.get_molecular_hamiltonian(occupied_indices=occupied, active_indices=act)
    else:
        mh = mol.get_molecular_hamiltonian()
    qh = jordan_wigner(get_fermion_operator(mh))
    terms = {}
    for term, coeff in qh.terms.items():
        c = float(np.real(coeff))
        if abs(c) > 1e-10:
            terms[term] = c
    nq = max((idx for t in terms for idx, _ in t), default=-1) + 1
    return terms, nq, mol


def _ansatz(theta, nq, layers, occupied):
    """Start from Hartree-Fock, then let the machine correct it."""
    circuit = q.QCircuit()
    for i in occupied:
        if i < nq:
            circuit << q.X(i)
    k = 0
    for _ in range(layers):
        for i in range(nq):
            circuit << q.RY(i, float(theta[k])); k += 1
        for i in range(nq):
            circuit << q.CNOT(i, (i + 1) % nq)
    for i in range(nq):
        circuit << q.RY(i, float(theta[k])); k += 1
    return circuit


def _groups(terms):
    """Pauli terms that can share one measurement basis are measured together."""
    buckets = {}
    for term, coeff in terms.items():
        if not term:
            continue
        basis = tuple(sorted(term))
        key = tuple(sorted({(i, p) for i, p in term}))
        buckets.setdefault(key, []).append((term, coeff))
    return buckets


def _measure_group(circuit, basis, nq, shots):
    prog = q.QProg()
    prog << circuit
    rot = q.QCircuit()
    for idx, pauli in basis:
        if pauli == "X":
            rot << q.H(idx)
        elif pauli == "Y":
            rot << q.RX(idx, pi / 2)
    prog << rot
    for c, qb in enumerate(range(nq)):
        prog << q.measure(qb, c)
    qvm = q.CPUQVM()
    qvm.run(prog, shots)
    return qvm.result().get_counts()


def _energy(theta, terms, nq, layers, occupied, shots):
    identity = terms.get((), 0.0)
    total = identity
    circuit = _ansatz(theta, nq, layers, occupied)
    for basis, group in _groups(terms).items():
        counts = _measure_group(circuit, basis, nq, shots)
        n = sum(counts.values()) or 1
        for term, coeff in group:
            idxs = [i for i, _ in term]
            acc = 0
            for raw, c in counts.items():
                bits = raw[::-1]
                parity = sum(int(bits[i]) for i in idxs if i < len(bits)) & 1
                acc += (-1 if parity else 1) * c
            total += coeff * acc / n
    return total


def experiment(p, shots):
    name = str(p.get("molecule", "H2"))
    if name not in MOLECULES:
        raise ValueError("molecule must be one of %s" % sorted(MOLECULES))
    spec = MOLECULES[name]
    layers = int(p.get("layers", 2))
    steps = int(p.get("search_steps", 200))
    vqe_shots = max(512, min(4096, int(p.get("vqe_shots", shots // 2))))
    lengths = p.get("bond_lengths")
    if not lengths:
        lengths = [float(p.get("bond_length", spec["default_length"]))]
    lengths = [float(x) for x in lengths][:9]
    active = p.get("active_space")
    if active:
        active = (list(active[0]), list(active[1]))
    elif name == "LiH":
        active = ([0], [1, 2, 3, 4])       # freeze the lithium core

    rows = []
    for length in lengths:
        terms, nq, mol = _hamiltonian(name, length, active)
        n_elec = mol.n_electrons if not active else 2
        occupied = list(range(min(n_elec, nq)))
        rng = np.random.default_rng(int(p.get("seed", 11)))
        best = None
        for attempt in range(int(p.get("restarts", 2))):
            theta0 = rng.uniform(-pi, pi, (layers + 1) * nq)
            r = minimize(_energy, theta0,
                         args=(terms, nq, layers, occupied, vqe_shots),
                         method="COBYLA",
                         options={"maxiter": max(steps, (layers + 1) * nq + 4),
                                  "rhobeg": 0.5})
            if best is None or r.fun < best:
                best = float(r.fun)
        rows.append({"bond_length": round(length, 4), "qubits": nq,
                     "pauli_terms": len(terms),
                     "vqe": round(best, 6),
                     "hartree_fock": round(float(mol.hf_energy), 6),
                     "exact": round(float(mol.fci_energy), 6),
                     "error_hartree": round(best - float(mol.fci_energy), 6),
                     "error_kcal_per_mol": round((best - float(mol.fci_energy)) * HARTREE_TO_KCAL, 3),
                     "recovered_correlation": round(
                         (float(mol.hf_energy) - best) /
                         max(1e-9, float(mol.hf_energy) - float(mol.fci_energy)), 4)})

    # a curve worth looking at
    display = [f"{name.upper()} — LOOKING FOR ITS GROUND STATE", "",
               spec["note"], ""]
    if len(rows) > 1:
        lo = min(r["exact"] for r in rows)
        hi = max(r["exact"] for r in rows)
        span = max(1e-9, hi - lo)
        display.append("  bond (A)    VQE (Ha)    exact      error")
        for r in rows:
            depth = int(round(28 * (r["exact"] - lo) / span))
            display.append(f"  {r['bond_length']:<10} {r['vqe']:<11} {r['exact']:<10} "
                           f"{r['error_hartree']:+.5f}  {' ' * depth}o")
        wells = min(rows, key=lambda r: r["exact"])
        display += ["", f"the well sits at {wells['bond_length']} A "
                        f"({wells['exact']} Ha) — that is the bond length"]
    else:
        r = rows[0]
        display += [f"  bond length      {r['bond_length']} A",
                    f"  qubits           {r['qubits']}  ({r['pauli_terms']} Pauli terms)",
                    f"  Hartree-Fock     {r['hartree_fock']} Ha   (the mean-field guess)",
                    f"  the machine      {r['vqe']} Ha",
                    f"  exact answer     {r['exact']} Ha",
                    "",
                    f"  off by {r['error_hartree']:+.6f} Ha "
                    f"({r['error_kcal_per_mol']:+.2f} kcal/mol)",
                    f"  it recovered {round(r['recovered_correlation']*100,1)}% of what "
                    f"mean-field misses"]

    return {
        "title": f"{name} looking for its ground state",
        "question": ("Did the machine find the true energy, and if it fell short, "
                     "where — near the bond, or out where the atoms are letting go "
                     "of each other?"),
        "reading_invitation": ("This one has a right answer, which is unusual here. "
                              "The gap between what it found and what is true is the "
                              "interesting quantity, not the energy itself."),
        "molecule": name, "basis": "sto-3g", "layers": layers,
        "gradeable": True,
        "results": rows,
        "display": display,
    }
