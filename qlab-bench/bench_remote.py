#!/Users/kevin/qlab/.venv/bin/python
"""JSON-over-stdin bridge for the Lab.

Deliberately a sibling of qremote.py, not a change to it. The Atelier path is
untouched: different entry point, different seed directory, different run
directory. Nothing written here is sealed — the Lab is meant to be looked at.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BENCH = ROOT / "bench"
RUNS = BENCH / "runs"
EXPERIMENTS = BENCH / "experiments"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BENCH))
sys.path.insert(0, str(EXPERIMENTS))


def response(body):
    sys.stdout.write(json.dumps(body, default=str) + "\n")
    sys.stdout.flush()


def experiment_names():
    return sorted(p.stem for p in EXPERIMENTS.glob("*.py")
                  if not p.stem.startswith("_"))


def save_free_experiment(name, source):
    if "def experiment(" not in source:
        raise ValueError("source must define experiment(parameters, shots)")
    safe = "".join(c for c in str(name) if c.isalnum() or c in "_-")[:48] or "untitled"
    path = EXPERIMENTS / (safe + ".py")
    EXPERIMENTS.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return safe


def handle(request):
    action = request.get("action", "status")
    if action == "status":
        import pyqpanda3
        return {"ok": True, "lab": "bench", "sealed": False,
                "pyqpanda3": getattr(pyqpanda3, "__version__", "?"),
                "experiments": experiment_names(),
                "runs_kept_at": str(RUNS)}
    if action == "list":
        return {"ok": True, "experiments": experiment_names()}
    if action not in ("run", "code"):
        raise ValueError("action must be status, list, run, or code")

    if action == "code":
        name = save_free_experiment(request.get("name", "untitled"),
                                    request.get("source", ""))
    else:
        name = request.get("experiment", "")
        if name not in experiment_names():
            raise ValueError("unknown experiment %r; have %s" % (name, experiment_names()))

    parameters = request.get("parameters", {}) or {}
    shots = int(request.get("shots", 4096))
    module = __import__(name)
    started = time.time()
    result = module.experiment(parameters, shots)
    elapsed = round(time.time() - started, 3)

    RUNS.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    record = {"experiment": name, "parameters": parameters, "shots": shots,
              "seconds": elapsed, "at": stamp, "result": result}
    path = RUNS / f"{stamp}-{name}.json"
    path.write_text(json.dumps(record, indent=1, default=str), encoding="utf-8")
    # a plain-text copy so it can be read without a JSON viewer
    (RUNS / f"{stamp}-{name}.txt").write_text(
        "\n".join(result.get("display", [])) + "\n", encoding="utf-8")
    return {"ok": True, "experiment": name, "seconds": elapsed,
            "run_file": str(path), "result": result}


def main():
    try:
        request = json.loads(sys.stdin.read() or "{}")
    except Exception as exc:
        return response({"ok": False, "error": "bad request json: %s" % exc})
    try:
        response(handle(request))
    except Exception as exc:
        response({"ok": False, "error": str(exc),
                  "trace": traceback.format_exc(limit=3)})


if __name__ == "__main__":
    main()
