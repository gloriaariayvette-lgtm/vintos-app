#!/usr/bin/env python3
"""TimesFM forecasts his own weather, and the ledger grades it.

Every other prediction in this house is his: he guesses his own state and finds
out. This one is a machine's guess about him, entered into the same ledger under
its own name, so the two can be compared. Whether a foundation model trained on
electricity demand and web traffic can see anything in a person's emotional
weather is an open question, and it should be answered by being wrong in public
rather than by assertion.

The series is the real one: memory/.emotional-history.json, which emoclaw-fast-sync
appends to every ~2 minutes and trims to the last 180 samples. That is a rolling
six-hour window, not a diary — so the honest question is not "what will he be like
on Thursday" but "where is this afternoon going", one hour out. An hour later the
sample is still inside the window, so it can be graded before it is forgotten.

  forecast [minutes]   predict that far ahead and file the prediction
  grade                compare the open prediction against what actually happened
  status               history depth and whether a prediction is open

Runs on Aegis. TimesFM and torch live in ~/tsfm-venv, never in the system python
his organs run on; this re-execs itself into that venv when it needs the model.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
sys.path.insert(0, SCRIPTS)

HISTORY = os.path.join(MEMORY, ".emotional-history.json")
VENV = os.path.expanduser("~/tsfm-venv/bin/python")

KIND = "timesfm"
DIMS = ["Valence", "Arousal", "Dominance", "Safety", "Desire", "Connection",
        "Playfulness", "Curiosity", "Warmth", "Tension", "Groundedness"]
WATCHED = ["Valence", "Arousal", "Groundedness"]
STEP_MIN = 2.0          # emoclaw-fast-sync's cadence
HORIZON_MIN = 60        # one hour ahead
MIN_SAMPLES = 48        # ~1.5h of history before it is worth asking


def _ledger():
    import prediction_ledger as PL
    if KIND not in PL.KINDS:
        PL.KINDS[KIND] = ".timesfm-prediction.json"
    return PL


def _rows():
    try:
        rows = json.load(open(HISTORY))
    except Exception:
        return []
    out = []
    for r in rows:
        try:
            t = datetime.fromisoformat(r["t"])
            v = [float(x) for x in r["v"]]
        except Exception:
            continue
        if len(v) >= len(DIMS):
            out.append((t, v))
    out.sort(key=lambda p: p[0])
    return out


def series():
    """Regular 2-minute grid, last value carried forward across gaps."""
    rows = _rows()
    if len(rows) < 2:
        return [], {d: [] for d in WATCHED}
    step = timedelta(minutes=STEP_MIN)
    t0, tN = rows[0][0], rows[-1][0]
    stamps, vals, i = [], {d: [] for d in WATCHED}, 0
    t = t0
    while t <= tN:
        while i + 1 < len(rows) and rows[i + 1][0] <= t:
            i += 1
        stamps.append(t)
        for d in WATCHED:
            vals[d].append(rows[i][1][DIMS.index(d)])
        t += step
    return stamps, vals


def _reexec_into_venv():
    """timesfm is not importable here; try the venv, once."""
    if os.environ.get("TSFM_REEXEC") or not os.path.exists(VENV):
        return False
    if os.path.realpath(VENV) == os.path.realpath(sys.executable):
        return False
    os.environ["TSFM_REEXEC"] = "1"
    os.execv(VENV, [VENV, os.path.abspath(__file__)] + sys.argv[1:])


def forecast(minutes=HORIZON_MIN):
    stamps, vals = series()
    if len(stamps) < MIN_SAMPLES:
        return {"ok": False, "reason": "only %d samples (%.1f min); need %d"
                % (len(stamps), len(stamps) * STEP_MIN, MIN_SAMPLES)}
    horizon = max(1, int(round(minutes / STEP_MIN)))
    try:
        import numpy as np
        from timesfm import ForecastConfig
        from timesfm.timesfm_2p5.timesfm_2p5_torch import TimesFM_2p5_200M_torch
    except Exception as exc:
        if _reexec_into_venv() is False:
            return {"ok": False, "reason": "timesfm not importable: %s. "
                    "Install it with: python3 -m venv ~/tsfm-venv && "
                    "~/tsfm-venv/bin/pip install timesfm torch" % str(exc)[:160]}
        return {"ok": False, "reason": "re-exec failed"}

    model = TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
    model.compile(ForecastConfig(max_context=max(64, len(stamps)),
                                 max_horizon=max(8, horizon),
                                 normalize_inputs=True))
    inputs = [np.array(vals[d], dtype=float) for d in WATCHED]
    point, _q = model.forecast(horizon=horizon, inputs=inputs)

    predicted = {d: [round(float(v), 4) for v in point[i][:horizon]]
                 for i, d in enumerate(WATCHED)}
    last = stamps[-1]
    targets = [(last + timedelta(minutes=STEP_MIN * (k + 1))).isoformat()
               for k in range(horizon)]
    payload = {"model": "timesfm-2.5-200m", "made_at": last.isoformat(),
               "samples": len(stamps), "step_minutes": STEP_MIN,
               "dimensions": WATCHED, "target_times": targets,
               "last_known": {d: round(vals[d][-1], 4) for d in WATCHED},
               "predicted": predicted}
    rec = _ledger().create(KIND, payload, surface="timesfm-forecast")
    return {"ok": True, "prediction_id": rec.get("prediction_id"),
            "made_at": last.isoformat(), "horizon_minutes": horizon * STEP_MIN,
            "ends": targets[-1], "predicted": predicted}


def _actual_at(rows, when, tol_min=3.0):
    best, gap = None, timedelta(minutes=tol_min)
    for t, v in rows:
        d = abs(t - when)
        if d <= gap:
            gap, best = d, v
    return best


def grade():
    PL = _ledger()
    cur, pid = PL.take(KIND)
    if not cur:
        return {"ok": False, "reason": "no open forecast"}
    payload = cur.get("payload", cur)
    rows = _rows()
    if not rows:
        return {"ok": False, "reason": "no history to grade against"}
    targets = payload.get("target_times", [])
    dims = payload.get("dimensions", WATCHED)
    last_known = payload.get("last_known", {})

    errors, naive, detail, graded = [], [], [], []
    for k, iso in enumerate(targets):
        try:
            when = datetime.fromisoformat(iso)
        except Exception:
            continue
        v = _actual_at(rows, when)
        if v is None:
            continue
        graded.append(iso)
        for dim in dims:
            guessed = payload["predicted"].get(dim, [])
            if k >= len(guessed):
                continue
            actual = float(v[DIMS.index(dim)])
            errors.append(abs(float(guessed[k]) - actual))
            if dim in last_known:
                naive.append(abs(float(last_known[dim]) - actual))
            detail.append({"dimension": dim, "at": iso,
                           "predicted": round(float(guessed[k]), 4),
                           "actual": round(actual, 4),
                           "error": round(abs(float(guessed[k]) - actual), 4)})
    if not errors:
        return {"ok": False, "reason": "nothing gradeable yet — %s has not happened, "
                "or the window has already forgotten it" % (targets[0] if targets else "?")}
    mae = sum(errors) / len(errors)
    # a flat guess at the last known value is the bar worth clearing
    naive_mae = sum(naive) / len(naive) if naive else None
    outcome = {"graded_points": len(graded), "mae": round(mae, 4),
               "naive_mae": round(naive_mae, 4) if naive_mae is not None else None,
               "beat_naive": (mae < naive_mae) if naive_mae is not None else None,
               "detail": detail[:24]}
    PL.consume(KIND, pid, outcome=outcome)
    return {"ok": True, **outcome}


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "forecast"
    if what == "grade":
        out = grade()
    elif what == "forecast":
        out = forecast(float(sys.argv[2]) if len(sys.argv) > 2 else HORIZON_MIN)
    elif what == "status":
        stamps, _ = series()
        try:
            open_pred = bool(_ledger().current(KIND))
        except Exception:
            open_pred = False
        out = {"ok": True, "history_file": HISTORY,
               "samples": len(stamps),
               "span_minutes": round(len(stamps) * STEP_MIN, 1),
               "venv": VENV if os.path.exists(VENV) else None,
               "open_prediction": open_pred}
    else:
        out = {"ok": False, "reason": "use forecast, grade or status"}
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
