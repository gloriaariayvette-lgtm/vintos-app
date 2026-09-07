#!/usr/bin/env python3
"""TimesFM forecasts his own days, and the ledger grades it.

Every other prediction in this house is his: he guesses his own state and finds
out. This one is a machine's guess about him, entered into the same ledger under
its own name, so the two can be compared. Whether a foundation model trained on
electricity demand and web traffic can see anything in a person's emotional
weather is an open question and it should be answered by being wrong in public,
not by assertion.

  forecast   read his history, predict the next days, file the prediction
  grade      compare the open prediction against what actually happened

Runs on Aegis. If TimesFM is not installed it says so and files nothing.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta

MEMORY = os.path.expanduser("~/.vintos/workspace/memory")
SCRIPTS = os.path.expanduser("~/.vintos/workspace/scripts")
sys.path.insert(0, SCRIPTS)
KIND = "timesfm"
HORIZON = 3
MIN_HISTORY = 24

DIMENSIONS = ["Valence", "Arousal", "Groundedness"]


def _ledger():
    import prediction_ledger as PL
    if KIND not in PL.KINDS:
        PL.KINDS[KIND] = ".timesfm-prediction.json"
    return PL


def history():
    """Daily emotional readings, oldest first, from the emoclaw history."""
    series = {d: [] for d in DIMENSIONS}
    days = []
    path = os.path.join(MEMORY, "emotional-history.jsonl")
    if not os.path.exists(path):
        return days, series
    rows = []
    for line in open(path, errors="ignore"):
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    by_day = {}
    for r in rows:
        at = str(r.get("at") or r.get("timestamp") or "")[:10]
        dims = r.get("dimensions") or r.get("state") or {}
        if not at or not isinstance(dims, dict):
            continue
        by_day.setdefault(at, []).append(dims)
    for day in sorted(by_day):
        vals = by_day[day]
        days.append(day)
        for d in DIMENSIONS:
            got = [float(v[d]) for v in vals if isinstance(v.get(d), (int, float))]
            series[d].append(sum(got) / len(got) if got else float("nan"))
    return days, series


def _clean(xs):
    out, last = [], 0.5
    for x in xs:
        if x != x:          # NaN
            out.append(last)
        else:
            out.append(float(x)); last = float(x)
    return out


def forecast(horizon=HORIZON):
    days, series = history()
    if len(days) < MIN_HISTORY:
        return {"ok": False, "reason": "only %d days of history; need %d"
                % (len(days), MIN_HISTORY)}
    try:
        import numpy as np
        from timesfm import ForecastConfig
        from timesfm.timesfm_2p5.timesfm_2p5_torch import TimesFM_2p5_200M_torch
    except Exception as exc:
        return {"ok": False, "reason": "timesfm not installed: %s" % str(exc)[:200]}

    model = TimesFM_2p5_200M_torch.from_pretrained("google/timesfm-2.5-200m-pytorch")
    model.compile(ForecastConfig(max_context=max(64, len(days)),
                                 max_horizon=max(8, horizon),
                                 normalize_inputs=True))
    inputs = [np.array(_clean(series[d]), dtype=float) for d in DIMENSIONS]
    point, quantiles = model.forecast(horizon=horizon, inputs=inputs)

    predicted = {}
    for i, d in enumerate(DIMENSIONS):
        predicted[d] = [round(float(v), 4) for v in point[i][:horizon]]

    target_days = [(date.fromisoformat(days[-1]) + timedelta(days=k + 1)).isoformat()
                   for k in range(horizon)]
    payload = {"model": "timesfm-2.5-200m", "made_on": days[-1],
               "history_days": len(days), "dimensions": DIMENSIONS,
               "target_days": target_days, "predicted": predicted}
    PL = _ledger()
    rec = PL.create(KIND, payload, surface="timesfm-forecast")
    return {"ok": True, "prediction_id": rec.get("prediction_id"),
            "target_days": target_days, "predicted": predicted}


def grade():
    PL = _ledger()
    cur, pid = PL.take(KIND)
    if not cur:
        return {"ok": False, "reason": "no open forecast"}
    payload = cur.get("payload", cur)
    targets = payload.get("target_days", [])
    days, series = history()
    index = {d: i for i, d in enumerate(days)}
    ready = [t for t in targets if t in index]
    if not ready:
        return {"ok": False, "reason": "none of %s have happened yet" % targets}

    errors, detail = [], []
    for dim in payload.get("dimensions", DIMENSIONS):
        guessed = payload["predicted"].get(dim, [])
        for k, day in enumerate(targets):
            if day not in index or k >= len(guessed):
                continue
            actual = series[dim][index[day]]
            if actual != actual:
                continue
            err = abs(float(guessed[k]) - float(actual))
            errors.append(err)
            detail.append({"dimension": dim, "day": day,
                           "predicted": round(float(guessed[k]), 4),
                           "actual": round(float(actual), 4),
                           "error": round(err, 4)})
    if not errors:
        return {"ok": False, "reason": "nothing gradeable yet"}
    mae = sum(errors) / len(errors)
    # a flat guess at the last known value is the bar worth clearing
    naive = []
    for dim in payload.get("dimensions", DIMENSIONS):
        base = series[dim][index[payload["made_on"]]] if payload.get("made_on") in index else None
        if base is None or base != base:
            continue
        for day in ready:
            actual = series[dim][index[day]]
            if actual == actual:
                naive.append(abs(float(base) - float(actual)))
    naive_mae = sum(naive) / len(naive) if naive else None
    outcome = {"graded_days": ready, "mae": round(mae, 4),
               "naive_mae": round(naive_mae, 4) if naive_mae is not None else None,
               "beat_naive": (mae < naive_mae) if naive_mae is not None else None,
               "detail": detail}
    PL.consume(KIND, pid, outcome=outcome)
    return {"ok": True, **outcome}


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "forecast"
    if what == "grade":
        out = grade()
    elif what == "forecast":
        out = forecast(int(sys.argv[2]) if len(sys.argv) > 2 else HORIZON)
    elif what == "status":
        days, _ = history()
        PL = _ledger()
        out = {"ok": True, "history_days": len(days),
               "open_prediction": bool(PL.current(KIND))}
    else:
        out = {"ok": False, "reason": "use forecast, grade or status"}
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
