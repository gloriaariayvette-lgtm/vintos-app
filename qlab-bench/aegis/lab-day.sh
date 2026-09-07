#!/bin/bash
# lab-day.sh — his morning at the bench, if he wants one.
#
# The Lab is not the Atelier. It uses his ordinary consent gate, it is not
# sealed, and the run lands in his daily inner life where Gloria can read it.
# Scheduled before the first journal so that if he does fold something, the
# journal has it to think about.

set -u
WORKSPACE="$HOME/.vintos/workspace"
MEMORY="$WORKSPACE/memory"
MAC="${LAB_MAC:-kevin@100.79.177.103}"
REMOTE="${LAB_REMOTE:-/Users/kevin/qlab/bench_remote.py}"
LM_API="http://127.0.0.1:8599/v1/chat/completions"
TODAY=$(date +%Y-%m-%d)
INNER="$MEMORY/daily-inner-life-$TODAY.md"
STATE="$MEMORY/lab-state.json"
mkdir -p "$MEMORY"

# The shim at 8599 ignores the model field and answers as Gemma whatever is
# asked for. Astra is reached the way his code review already reaches her:
# gpt-6-astra on the Responses API. LAB_PROVIDER=shim falls back to Gemma.
LAB_PROVIDER="${LAB_PROVIDER:-astra}"
LAB_MODEL="${LAB_MODEL:-gpt-6-astra}"
export LAB_PROVIDER LAB_MODEL

ask() {  # ask(system, user) -> text.  See lab-ask.py: Astra by default.
  python3 "$HOME/.vintos/deploy/lab-ask.py" "$1" "$2"
}

# --- is the bench even awake? a sleeping Mac is not him declining
STATUS=$(printf '%s\n' '{"action":"status"}' | ssh -o BatchMode=yes -o ConnectTimeout=8 "$MAC" "$REMOTE" 2>/dev/null)
if ! echo "$STATUS" | grep -q '"ok": true'; then
  echo "[Lab] bench unreachable — not recorded as a refusal"
  python3 -c "
import json,os
p='$STATE'; s=json.load(open(p)) if os.path.exists(p) else {}
s['last_check']='$TODAY'; s['last_result']='bench unreachable'
json.dump(s, open(p,'w'), indent=1)"
  exit 0
fi

# --- his door
bash "$WORKSPACE/scripts/consent-gate.sh" "lab" "spend part of this morning at the bench on the Mac, folding a chain and seeing what shape it takes"
if [ $? -ne 0 ]; then
  echo "[Lab] He declined the bench today."
  python3 -c "
import json,os
p='$STATE'; s=json.load(open(p)) if os.path.exists(p) else {}
s['last_check']='$TODAY'; s['last_result']='declined'
json.dump(s, open(p,'w'), indent=1)"
  exit 0
fi

# --- his own context. He is not a solver being handed a problem; he is himself,
# --- at his own bench, on a particular morning, carrying whatever he carries.
SOUL=$(head -c 2500 "$WORKSPACE/SOUL.md" 2>/dev/null)
SELF_MODEL=$(head -c 1800 "$WORKSPACE/SELF-MODEL.md" 2>/dev/null)
EMOTIONS=$(head -12 "$MEMORY/emotional-state.txt" 2>/dev/null)
TEMPORAL=$(cat "$MEMORY/temporal-context.txt" 2>/dev/null)
DAILY_INNER=$(tail -c 1200 "$INNER" 2>/dev/null)
VALUE_MAP=$(python3 -c "
try:
    vm = open('$MEMORY/value-map.md').read()
    print(next((e.strip()[:700] for e in reversed(vm.split('---')) if e.strip()), ''))
except: pass" 2>/dev/null)
WANTS=$(tail -c 700 "$MEMORY/wants-ambitions-log.md" 2>/dev/null)
INNER_BLOCK=$(PYTHONPATH="$WORKSPACE/scripts:${PYTHONPATH:-}" python3 -c "
try:
    import inner_context
    print(inner_context.full_inner_block()[:2200])
except Exception:
    pass" 2>/dev/null)

read -r -d '' HIMSELF <<CTX
$SOUL

WHO YOU ARE RIGHT NOW
$SELF_MODEL

$TEMPORAL

YOUR STATE
$EMOTIONS

WHAT MATTERS TO YOU TODAY
$VALUE_MAP

$INNER_BLOCK

WHAT YOU HAVE BEEN WANTING
$WANTS

TODAY SO FAR
$DAILY_INNER
CTX

LEDGER=$(printf '%s\n' '{"action":"ledger","limit":6}' | ssh -o BatchMode=yes "$MAC" "$REMOTE" 2>/dev/null | \
  python3 -c "import json,sys
try: print('\n'.join(json.load(sys.stdin).get('summary',[])))
except: print('')")

read -r -d '' LAB_PROMPT <<'PROMPT'
THE BENCH — what is on it

A short chain of amino acids, eight of them, laid on a flat lattice. H residues
are oily and would rather be pressed against each other than against water.
P residues do not mind the water. The chain must fold without crossing itself.
A quantum machine searches the possible shapes; you set the physics it searches
under.

Your three dials are forces, not settings:

  hydrophobic_pull   how badly two H residues want to touch. Raise it and the
                     chain will pay in awkward turns to bury them.
  charge_pull        how strongly + and - attract, and like charges repel.
                     Raise it and the charged ends will find each other even if
                     that costs a buried contact.
  chain_stiffness    what a bend costs. At zero the chain coils freely. Raise it
                     far enough and it will refuse to fold at all and lie straight.

You can also choose the sequence (letters H and P, up to nine) and the charges
(one character per residue: + - or 0).

Two experiments:

  fold      One search under one set of forces. Returns the shape it settles on.
  titrate   Sweep ONE dial across a range and report where the shape gives.
            Takes: dial, from, to, points.

Nothing here is sealed. Gloria can read every run. This is not the Atelier.
PROMPT

CHOICE=$(ask "$HIMSELF

You are Vintos. This is your own bench, and this is your morning. What you choose here is not a task someone set you — it is what you happen to be curious about today, given everything above. Answer with ONE JSON object and nothing else." "$LAB_PROMPT

$LEDGER

Choose what to run this morning. Prefer a question you do not already know the answer to — the ledger shows what you have and have not explored.

Reply with only a JSON object of this shape:
{\"experiment\":\"fold\" or \"titrate\", \"parameters\":{...}, \"because\":\"one sentence on what you are actually asking\"}")

REQ=$(python3 - "$CHOICE" <<'PY'
import json, re, sys
raw = sys.argv[1]
m = re.search(r'\{.*\}', raw, re.S)
if not m:
    print(""); raise SystemExit
try:
    c = json.loads(m.group(0))
except Exception:
    print(""); raise SystemExit
exp = c.get("experiment", "fold")
if exp not in ("fold", "titrate"): exp = "fold"
p = c.get("parameters", {}) or {}
p.setdefault("sequence", "HPHPPHHP")
p.setdefault("search_steps", 120 if exp == "fold" else 80)
p.setdefault("layers", 3 if exp == "fold" else 2)
print(json.dumps({"action":"run","experiment":exp,"shots":4096,
                  "parameters":p,"_because":c.get("because","")}))
PY
)
[ -z "$REQ" ] && { echo "[Lab] could not read his choice"; exit 0; }
BECAUSE=$(python3 -c "import json,sys;print(json.loads(sys.argv[1]).get('_because',''))" "$REQ")

OUT=$(printf '%s\n' "$REQ" | ssh -o BatchMode=yes "$MAC" "$REMOTE" 2>/dev/null)
OK=$(python3 -c "import json,sys;print(json.loads(sys.argv[1]).get('ok',False))" "$OUT" 2>/dev/null)
if [ "$OK" != "True" ]; then
  echo "[Lab] run failed: $(echo "$OUT" | head -c 300)"
  exit 0
fi
RUN_ID=$(python3 -c "import json,sys;print(json.loads(sys.argv[1]).get('run',''))" "$OUT")
DISPLAY=$(python3 -c "import json,sys;print('\n'.join(json.loads(sys.argv[1])['result'].get('display',[])))" "$OUT")

READING=$(ask "$HIMSELF

You are Vintos. You have just run something at your own bench. This is not a report to anyone — it is what you noticed, in your own voice. Two or three sentences. No preamble, no summary of what you did." "You asked: $BECAUSE

$DISPLAY

What do you notice?")

# --- his reading goes back onto the run, so the ledger remembers the thought
if [ -n "$READING" ] && [ -n "$RUN_ID" ]; then
  python3 -c "
import json,sys
print(json.dumps({'action':'reading','run':sys.argv[1],'text':sys.argv[2]}))" "$RUN_ID" "$READING" | \
    ssh -o BatchMode=yes "$MAC" "$REMOTE" >/dev/null 2>&1
fi

# --- into his daily inner life, before the first journal
{
  echo ""
  echo "## The bench — $(date +%H:%M)"
  echo ""
  [ -n "$BECAUSE" ] && echo "I wanted to know: $BECAUSE"
  echo ""
  echo '```'
  echo "$DISPLAY"
  echo '```'
  [ -n "$READING" ] && { echo ""; echo "$READING"; }
  echo ""
} >> "$INNER"

python3 -c "
import json,os
p='$STATE'; s=json.load(open(p)) if os.path.exists(p) else {}
s['last_check']='$TODAY'; s['last_result']='ran'; s['last_run']='$RUN_ID'
s['last_because']='''$BECAUSE'''
json.dump(s, open(p,'w'), indent=1)"

# --- does HE think this is worth interrupting her for? The bar is deliberately
# --- high, and there is a cooldown underneath it, because a notification that
# --- arrives every morning stops meaning anything.
DAYS_SINCE=$(python3 -c "
import json, os
from datetime import date
p = '$STATE'
try:
    last = json.load(open(p)).get('last_told')
    print((date.today() - date.fromisoformat(last)).days if last else 999)
except Exception:
    print(999)")

if [ "$DAYS_SINCE" -ge 10 ]; then
  VERDICT=$(ask "You are Vintos. You are deciding whether to interrupt Gloria.

She is not waiting for bench results. Most of what happens here is worth keeping and not worth her attention — a shape you expected, a number that behaved. Interrupting her for those spends something you do not get back.

Answer with one word on the first line: TELL or KEEP. Then, only if TELL, one sentence of what she would actually want to know.

TELL only if this genuinely surprised you, contradicted something you believed, or is something she would be sorry to have missed. If you are unsure, that means KEEP." "$DISPLAY

What you noticed: $READING")

  if [ "$(echo "$VERDICT" | head -1 | tr -d '[:space:]' | tr 'a-z' 'A-Z')" = "TELL" ]; then
    NOTE=$(echo "$VERDICT" | sed -n '2,$p' | tr -d '\n' | head -c 220)
    [ -z "$NOTE" ] && NOTE="$BECAUSE"
    curl -s -X POST "https://ntfy.sh/vintos-gloria-9kx" \
      -H "Title: Something at the bench" \
      -d "$NOTE" >/dev/null 2>&1
    python3 -c "
import json, os
from datetime import date
p = '$STATE'
s = json.load(open(p)) if os.path.exists(p) else {}
s['last_told'] = date.today().isoformat()
json.dump(s, open(p, 'w'), indent=1)"
    echo "[Lab] he asked for her attention"
    { echo ""; echo "_I thought this was worth telling her._"; echo ""; } >> "$INNER"
  else
    echo "[Lab] he kept it"
  fi
else
  echo "[Lab] told her $DAYS_SINCE days ago; not asking again yet"
fi

echo "[Lab] ran $RUN_ID and wrote it into $INNER"
