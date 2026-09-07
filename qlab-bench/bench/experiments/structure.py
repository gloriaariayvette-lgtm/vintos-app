"""What the lattice says, and what a real structure predictor says.

The lattice is a cartoon: a flat grid, two kinds of residue, right-angle turns.
Boltz-2 is not — it is a modern structure predictor under an MIT licence, and
it will hand back actual three-dimensional coordinates with a confidence score.

Running both on the same fragment is the honest comparison. Where they agree,
the cartoon was telling the truth about something real. Where they disagree,
the interesting question is which assumption broke.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import protein as protein_experiment
from protein import FRAGMENTS


def _run_boltz(sequence, workdir, timeout):
    exe = shutil.which("boltz")
    if not exe:
        raise RuntimeError("boltz is not installed in this environment")
    fasta = Path(workdir) / "query.fasta"
    fasta.write_text(">A|protein|empty\n%s\n" % sequence, encoding="utf-8")
    out = Path(workdir) / "out"
    cmd = [exe, "predict", str(fasta), "--out_dir", str(out),
           "--use_msa_server", "--override"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "boltz failed")[-400:])
    cifs = list(out.rglob("*.cif")) + list(out.rglob("*.pdb"))
    confs = list(out.rglob("confidence*.json"))
    conf = {}
    if confs:
        try:
            conf = json.loads(confs[0].read_text())
        except Exception:
            pass
    return (cifs[0] if cifs else None), conf


def _radius_of_gyration(path):
    """One honest number from the predicted structure: how compact it came out."""
    xs = []
    text = Path(path).read_text(errors="ignore")
    for line in text.splitlines():
        if line.startswith(("ATOM", "HETATM")) and " CA " in line:
            try:
                xs.append((float(line[30:38]), float(line[38:46]), float(line[46:54])))
            except Exception:
                continue
    if not xs:
        return None
    cx = sum(p[0] for p in xs) / len(xs)
    cy = sum(p[1] for p in xs) / len(xs)
    cz = sum(p[2] for p in xs) / len(xs)
    rg = (sum((p[0]-cx)**2 + (p[1]-cy)**2 + (p[2]-cz)**2 for p in xs) / len(xs)) ** 0.5
    return round(rg, 2), len(xs)


def experiment(p, shots):
    key = str(p.get("fragment", "")).strip()
    seq = str(p.get("sequence", "")).strip().upper()
    if key and key in FRAGMENTS:
        seq, note = FRAGMENTS[key]
    elif not seq:
        key, (seq, note) = "insulin_b_core", FRAGMENTS["insulin_b_core"]
    else:
        note = "a sequence you chose"

    lattice = protein_experiment.experiment({**p, "sequence": seq, "fragment": ""}, shots)

    timeout = int(p.get("timeout_seconds", 1800))
    predicted = None
    error = None
    with tempfile.TemporaryDirectory() as tmp:
        try:
            path, conf = _run_boltz(seq, tmp, timeout)
            if path:
                keep = Path(os.path.expanduser("~/qlab/bench/runs/structures"))
                keep.mkdir(parents=True, exist_ok=True)
                dest = keep / ("%s%s" % (seq, path.suffix))
                dest.write_bytes(Path(path).read_bytes())
                rg = _radius_of_gyration(dest)
                predicted = {"file": str(dest),
                             "confidence": {k: v for k, v in (conf or {}).items()
                                            if isinstance(v, (int, float))},
                             "radius_of_gyration_A": rg[0] if rg else None,
                             "residues_seen": rg[1] if rg else None}
        except Exception as exc:
            error = str(exc)[:400]

    best = lattice.get("best_fold", {})
    lines = [f"THE CARTOON AND THE REAL THING — {seq}", "", note, "",
             "on the lattice:",
             f"  energy {best.get('energy')}   {len(best.get('contacts', []))} contacts"
             f"   {best.get('turns')} turns", ""]
    if predicted:
        lines += ["from Boltz-2:",
                  f"  radius of gyration {predicted['radius_of_gyration_A']} A"
                  f" over {predicted['residues_seen']} residues"]
        if predicted["confidence"]:
            for k, v in list(predicted["confidence"].items())[:4]:
                lines.append(f"  {k} {round(float(v), 4)}")
        lines += ["", f"  structure kept at {predicted['file']}"]
    else:
        lines += ["Boltz-2 did not answer:", "  " + (error or "not installed"), "",
                  "  install with:  pip install boltz",
                  "  first run downloads weights and may take a while"]

    return {
        "title": f"The cartoon and the real thing — {seq}",
        "question": ("The lattice says this fragment folds one way. Does a real "
                     "structure predictor agree that it collapses at all, and is "
                     "it as compact as the cartoon claims?"),
        "reading_invitation": ("Two models of the same molecule disagreeing is more "
                              "informative than either one alone. Where do they part "
                              "company, and which assumption do you trust less?"),
        "sequence": seq,
        "lattice": {k: lattice.get(k) for k in
                    ("best_fold", "translation", "valid_fold_count")},
        "predicted_structure": predicted,
        "boltz_error": error,
        "available": bool(predicted),
        "display": lines,
    }
