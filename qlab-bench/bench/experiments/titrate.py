"""Turn one dial slowly and watch for the moment the shape gives.

A single fold is an answer. A titration is a question: at what stiffness does
this chain stop being willing to coil? Chemistry is full of these thresholds
and they are rarely where you expect, which is the whole reason to sweep
rather than to guess.
"""
from __future__ import annotations

from benchlib import fold_energy, draw, parse_sequence, parse_charges, exact_best
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

    charges = parse_charges(p.get("charges"), len(sequence))
    hp = float(p.get("hydrophobic_pull", 1.0))
    cw = float(p.get("charge_pull", 0.5))
    tw = float(p.get("chain_stiffness", 0.15))
    overlap_penalty = float(p.get("overlap_penalty", 3.0))
    fixed = {"hydrophobic_pull": hp, "charge_pull": cw, "chain_stiffness": tw}

    rows = []
    for i in range(steps):
        value = lo + (hi - lo) * i / (steps - 1)
        params = dict(base); params[dial] = round(value, 4)
        r = fold_experiment.experiment(params, per_shots)
        best = r["best_fold"]

        # the truth, by exhaustion, so a stuck search cannot pass for an answer
        dials = dict(fixed); dials[dial] = value
        truth = exact_best(sequence, charges, dials["hydrophobic_pull"],
                           dials["charge_pull"], dials["chain_stiffness"],
                           overlap_penalty)
        row = {"value": round(value, 4), "energy": best["energy"],
               "contacts": len(best["contacts"]), "turns": best["turns"],
               "valid_folds": r["valid_fold_count"],
               "coords": best["coords"]}
        if truth:
            row["exact_energy"] = truth["energy"]
            row["exact_turns"] = truth["turns"]
            row["exact_contacts"] = len(truth["contacts"])
            row["exact_coords"] = truth["coords"]
            row["gap"] = round(float(best["energy"]) - float(truth["energy"]), 4)
            row["found_it"] = row["gap"] <= 1e-6
        rows.append(row)

    # where did the shape actually change?
    have_truth = all("exact_energy" in r for r in rows)
    tk, ck = ("exact_turns", "exact_contacts") if have_truth else ("turns", "contacts")
    breaks = []
    for a, b in zip(rows, rows[1:]):
        if a[tk] != b[tk] or a[ck] != b[ck]:
            breaks.append({"between": [a["value"], b["value"]],
                           "turns": [a[tk], b[tk]],
                           "contacts": [a[ck], b[ck]]})

    display = [f"TURNING THE {dial.replace('_',' ').upper()}", "",
               f"sequence {sequence}   swept {lo} -> {hi} in {steps} steps", ""]
    for r in rows:
        c = r.get("exact_contacts", r["contacts"])
        bar = "#" * max(0, int(c * 3)) or "."
        if "exact_energy" in r:
            mark = "" if r["found_it"] else f"   [search stuck, off by {r['gap']}]"
            display.append(f"  {dial.split('_')[-1]:>9} {r['value']:<6} "
                           f"energy {r['exact_energy']:>7}  turns {r['exact_turns']}  "
                           f"contacts {c} {bar}{mark}")
        else:
            display.append(f"  {dial.split('_')[-1]:>9} {r['value']:<6} "
                           f"energy {r['energy']:>7}  turns {r['turns']}  "
                           f"contacts {c} {bar}")
    display += [""]
    if have_truth:
        missed = sum(1 for r in rows if not r["found_it"])
        display.append(f"the shapes above are exact — every one of the "
                       f"{1 << (2 * (len(sequence) - 2))} possible folds was checked.")
        display.append(f"the quantum search matched the exact answer at "
                       f"{len(rows) - missed} of {len(rows)} points"
                       + ("." if not missed else f"; at the other {missed} it got stuck."))
        display.append("")
    if breaks:
        for b in breaks:
            display.append(f"the shape gave between {b['between'][0]} and {b['between'][1]}"
                           f"  (turns {b['turns'][0]}->{b['turns'][1]},"
                           f" contacts {b['contacts'][0]}->{b['contacts'][1]})")
    else:
        display.append("the shape held across the whole sweep — try a wider range")
    display += ["", "at the far end:"] + draw(
        rows[-1].get("exact_coords", rows[-1]["coords"]), sequence)

    return {
        "title": f"Turning the {dial.replace('_',' ')}",
        "question": ("Is there a value where this chain changes its mind about "
                     "how to fold, and is it where you would have guessed?"),
        "reading_invitation": ("A threshold is more interesting than a number. "
                               "What do you make of where it sits, or of its absence?"),
        "sequence": sequence, "dial": dial, "swept": [lo, hi], "points": steps,
        "curve": [{k: r[k] for k in
                   ("value", "energy", "contacts", "turns", "valid_folds",
                    "exact_energy", "exact_turns", "exact_contacts", "gap", "found_it")
                   if k in r} for r in rows],
        "exact": have_truth,
        "search_matched_exact": (sum(1 for r in rows if r.get("found_it")) if have_truth else None),
        "shape_changes": breaks,
        "display": display,
    }
