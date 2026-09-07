"""Take a real protein sequence and put it on the bench.

The lattice game speaks in H and P — oily and not. Real proteins speak in
twenty letters. This translates: each amino acid gets its H or P from measured
hydrophobicity (Kyte and Doolittle, 1982) and its charge from what it actually
carries at blood pH. So he can fold a real fragment — a piece of insulin, the
core of a zinc finger — rather than an invented string.

No neural network is needed for the translation; hydrophobicity is a measured
property, not a prediction. ESM3 is optional and does something different: it
proposes NEW sequences worth folding, which is a question rather than a lookup.
"""
from __future__ import annotations

import fold as fold_experiment

# Kyte-Doolittle hydropathy. Positive is water-avoiding.
HYDROPATHY = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5,
    "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8,
    "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}
# Net charge at physiological pH.
CHARGE = {"D": -1, "E": -1, "K": 1, "R": 1, "H": 0}

FRAGMENTS = {
    "insulin_b_core": ("LVEALYLV", "the hydrophobic middle of insulin's B chain"),
    "zinc_finger":    ("FQCRICMR", "the metal-binding core of a zinc finger"),
    "amyloid_core":   ("KLVFFAED", "the segment of amyloid-beta that drives aggregation"),
    "collagen_rep":   ("GPPGPPGP", "collagen's repeat; proline everywhere, famously stiff"),
    "polyalanine":    ("AAAAAAAA", "a control — nothing distinguishes one end from the other"),
}


def translate(seq, threshold=1.0):
    seq = "".join(c for c in str(seq).upper() if c in HYDROPATHY)[:9]
    hp = "".join("H" if HYDROPATHY[c] >= threshold else "P" for c in seq)
    charges = "".join({1: "+", -1: "-"}.get(CHARGE.get(c, 0), "0") for c in seq)
    return seq, hp, charges


def experiment(p, shots):
    key = str(p.get("fragment", "")).strip()
    raw = str(p.get("sequence", "")).strip()
    if key and key in FRAGMENTS:
        raw, note = FRAGMENTS[key]
    elif raw:
        note = "a sequence you chose"
    else:
        key = "insulin_b_core"
        raw, note = FRAGMENTS[key]

    threshold = float(p.get("hydrophobic_threshold", 1.0))
    seq, hp, charges = translate(raw, threshold)
    if len(hp) < 4:
        raise ValueError("need at least four recognisable amino acids")

    params = dict(p)
    params.pop("fragment", None)
    params["sequence"] = hp
    params["charges"] = charges
    params.setdefault("layers", 3)
    params.setdefault("search_steps", 120)
    result = fold_experiment.experiment(params, shots)

    rows = []
    for i, c in enumerate(seq):
        rows.append(f"  {c}  hydropathy {HYDROPATHY[c]:+5.1f}  -> {hp[i]}"
                    f"{'   charge ' + charges[i] if charges[i] != '0' else ''}")

    result["title"] = f"Folding {raw}"
    result["real_sequence"] = seq
    result["fragment_note"] = note
    result["translation"] = {"hydropathy_threshold": threshold,
                             "hp": hp, "charges": charges}
    result["question"] = ("This is a real fragment. Does the shape it settles into "
                          "put the oily residues where you would expect, and does "
                          "that tell you anything about why the real molecule "
                          "behaves as it does?")
    result["display"] = ([f"FOLDING {raw}", "", note, "",
                          "how the letters translate:"] + rows +
                         ["", f"  -> lattice sequence {hp}   charges {charges}", ""] +
                         result["display"][2:])
    return result
