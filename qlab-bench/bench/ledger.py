"""What happened at the bench before.

Not an archive — a memory. It answers the only questions worth asking across
runs: which dials has he tried, what shape came out, and did he say anything
about it afterwards. Kept short on purpose; a ledger nobody reads is a log.
"""
from __future__ import annotations

import json
from pathlib import Path

RUNS = Path(__file__).resolve().parent / "runs"


def _load(limit=200):
    rows = []
    for p in sorted(RUNS.glob("*.json"), reverse=True)[:limit]:
        try:
            rows.append((p, json.loads(p.read_text(encoding="utf-8"))))
        except Exception:
            continue
    return rows


def entries(limit=40):
    out = []
    for path, rec in _load():
        r = rec.get("result", {})
        best = r.get("best_fold", {}) or {}
        out.append({
            "at": rec.get("at"),
            "experiment": rec.get("experiment"),
            "run": path.stem,
            "dials": r.get("dials", rec.get("parameters", {})),
            "sequence": r.get("sequence"),
            "energy": best.get("energy"),
            "contacts": len(best.get("contacts", []) or []),
            "turns": best.get("turns"),
            "valid_folds": r.get("valid_fold_count"),
            "search": (r.get("search", {}) or {}).get("final_energy"),
            "reading": rec.get("reading"),
        })
        if len(out) >= limit:
            break
    return out


def summary(limit=8):
    """A compact block for his context. Facts he can disagree with."""
    rows = entries(limit)
    if not rows:
        return ["THE BENCH", "", "Nothing has been run here yet."]
    lines = ["THE BENCH — what you have tried", ""]
    for e in rows:
        d = e["dials"] or {}
        dial_text = "  ".join(
            f"{k.replace('_',' ')} {v}" for k, v in d.items()
            if k in ("hydrophobic_pull", "charge_pull", "chain_stiffness"))
        lines.append(f"{e['at']}  {e['experiment']}  {e.get('sequence') or ''}")
        if dial_text:
            lines.append(f"    {dial_text}")
        if e["energy"] is not None:
            lines.append(f"    -> energy {e['energy']}, {e['contacts']} contacts, "
                         f"{e['turns']} turns, {e['valid_folds']} valid folds seen")
        if e.get("reading"):
            first = str(e["reading"]).strip().splitlines()[0][:96]
            lines.append(f"    you said: {first}")
        lines.append("")
    # what has actually been explored, so he can notice a gap
    seen = [e["dials"] or {} for e in entries(200)]
    def span(k):
        vals = [float(s[k]) for s in seen if k in s and s[k] is not None]
        return (min(vals), max(vals)) if vals else None
    ranges = {k: span(k) for k in ("hydrophobic_pull", "charge_pull", "chain_stiffness")}
    tried = [f"{k.replace('_',' ')} {v[0]}–{v[1]}" for k, v in ranges.items() if v]
    if tried:
        lines += ["you have only explored: " + ";  ".join(tried), ""]
    return lines


def attach_reading(run_stem, text):
    path = RUNS / (run_stem + ".json")
    if not path.exists():
        raise ValueError("no such run: %s" % run_stem)
    rec = json.loads(path.read_text(encoding="utf-8"))
    rec["reading"] = text
    path.write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
    txt = RUNS / (run_stem + ".txt")
    if txt.exists():
        txt.write_text(txt.read_text(encoding="utf-8").rstrip() +
                       "\n\n--- his reading ---\n" + text.rstrip() + "\n", encoding="utf-8")
    return {"ok": True, "run": run_stem}
