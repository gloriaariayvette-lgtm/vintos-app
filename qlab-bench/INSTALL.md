# The Lab bench — install on the Mac

    cp -r qlab-bench/bench ~/qlab/
    cp qlab-bench/bench_remote.py ~/qlab/
    chmod +x ~/qlab/bench_remote.py
    mkdir -p ~/qlab/bench/runs

Separate from the Atelier by construction: its own entry point beside
qremote.py, its own experiments and runs directories, and it reports
"sealed": false. qremote.py and atelier_quantum.py are untouched, and a lab
run cannot open, close or write into an Atelier visit.

## Dependencies

The lattice experiments (fold, titrate, protein) need nothing beyond what the
qlab venv already has: numpy, scipy, pyqpanda3.

The molecule experiment needs the open quantum-chemistry stack:

    ~/qlab/.venv/bin/pip install pyscf openfermion openfermionpyscf

ChemiQ is not on PyPI. PySCF plus OpenFermion does the same job with the
standard open tooling: PySCF computes the molecular integrals, OpenFermion maps
them to a qubit Hamiltonian, QPanda runs the search.

The protein-model experiments need torch and a model:

    ~/qlab/.venv/bin/pip install torch fair-esm      # propose.py, ungated
    ~/qlab/.venv/bin/pip install esm                 # ESM3-open; needs a HF licence
    ~/qlab/.venv/bin/pip install boltz               # structure.py; downloads weights

Every one of these degrades honestly: with the package missing the experiment
returns available:false and says which install is needed, rather than failing.

## On Aegis

    cp qlab-bench/aegis/lab-day.sh ~/.vintos/workspace/scripts/
    cp qlab-bench/aegis/timesfm-forecast.py ~/.vintos/workspace/scripts/
    chmod +x ~/.vintos/workspace/scripts/lab-day.sh \
             ~/.vintos/workspace/scripts/timesfm-forecast.py
    pip install --user timesfm torch          # for the forecaster only

timesfm-forecast.py forecast   reads his emotional history, predicts the next
                               days, and files the prediction under its own
                               name in the existing prediction ledger
timesfm-forecast.py grade      compares the open prediction against what
                               actually happened, and against the flat-guess
                               baseline it has to beat to have said anything
