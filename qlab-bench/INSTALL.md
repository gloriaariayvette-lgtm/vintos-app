# The Lab bench — install on the Mac

    cp -r qlab-bench/bench ~/qlab/
    cp qlab-bench/bench_remote.py ~/qlab/
    chmod +x ~/qlab/bench_remote.py
    mkdir -p ~/qlab/bench/runs

Separate from the Atelier by construction: its own entry point beside
qremote.py, its own experiments and runs directories, and it reports
"sealed": false. qremote.py and atelier_quantum.py are untouched, and a lab
run cannot open, close or write into an Atelier visit.
