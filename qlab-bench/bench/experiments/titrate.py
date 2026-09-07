"""Turn one dial slowly and watch for the moment the shape gives.

A single fold is an answer. A titration is a question: at what stiffness does
this chain stop being willing to coil? Chemistry is full of these thresholds
and they are rarely where you expect, which is the whole reason to sweep
rather than to guess.
"""
from __future__ import annotations

from benchlib import fold_energy, draw, parse_sequence, parse_charges
import fold as fold_experiment


def experiment(p, shots):
    sequence = parse_sequence(p.get("sequence"), "HPHPPHHP")
    dial = str(p.get("dial", "chain_stiffness"))
    if dial not in ("chain_stiffness", "charge_pull", "hydrophobic_pull"):
        raise ValueError("dial must be chain_stiffness, charge_pull or hydrophobic_pull")
    lo = float(p.get("from", 0.0))
    hi = float(p.get("to", 0.8))
    steps = max(2, min(9, int(p.get("points", 5))))
    per_shots = max(512, shots // steps)

    base = {k: p[k] for k in
            ("sequence", "charges", "hydrophobic_pull", "charge_pull",
             "chain_stiffness", "layers", "overlap_penalty", "tail") if k in p}
    base.setdefault("search_steps", int(p.get("search_steps", 80)))

    rows = []
    for i in range(steps):
        value = lo + (hi - lo) * i / (steps - 1)
        params = dict(base); params[dial] = round(value, 4)
        r = fold_experiment.experiment(params, per_shots)
        best = r["best_fold"]
        rows.append({"value": round(value, 4), "energy": best["energy"],
                     "contacts": len(best["contacts"]), "turns": best["turns"],
                     "valid_folds": r["valid_fold_count"],
                     "coords": best["coords"]})

    # where did the shape actually change?
    breaks = []
    for a, b in zip(rows, rows[1:]):
        if a["turns"] != b["turns"] or a["contacts"] != b["contacts"]:
            breaks.append({"between": [a["value"], b["value"]],
                           "turns": [a["turns"], b["turns"]],
                           "contacts": [a["contacts"], b["contacts"]]})

    display = [f"TURNING THE {dial.replace('_',' ').upper()}", "",
               f"sequence {sequence}   swept {lo} -> {hi} in {steps} steps", ""]
    for r in rows:
        bar = "#" * max(0, int(r["contacts"] * 3)) or "."
        display.append(f"  {dial.split('_')[-1]:>9} {r['value']:<6} "
                       f"energy {r['energy']:>7}  turns {r['turns']}  "
                       f"contacts {r['contacts']} {bar}")
    display += [""]
    if breaks:
        for b in breaks:
            display.append(f"the shape gave between {b['between'][0]} and {b['between'][1]}"
                           f"  (turns {b['turns'][0]}->{b['turns'][1]},"
                           f" contacts {b['contacts'][0]}->{b['contacts'][1]})")
    else:
        display.append("the shape held across the whole sweep — try a wider range")
    display += ["", "at the far end:"] + draw(rows[-1]["coords"], sequence)

    return {
        "title": f"Turning the {dial.replace('_',' ')}",
        "question": ("Is there a value where this chain changes its mind about "
                     "how to fold, and is it where you would have guessed?"),
        "reading_invitation": ("A threshold is more interesting than a number. "
                               "What do you make of where it sits, or of its absence?"),
        "sequence": sequence, "dial": dial, "swept": [lo, hi], "points": steps,
        "curve": [{k: r[k] for k in ("value", "energy", "contacts", "turns", "valid_folds")}
                  for r in rows],
        "shape_changes": breaks,
        "display": display,
    }
