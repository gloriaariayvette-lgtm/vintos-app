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
