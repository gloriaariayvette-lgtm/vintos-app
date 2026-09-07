# The Lab on Aegis

    cp qlab-bench/aegis/lab-day.sh ~/.vintos/workspace/scripts/
    chmod +x ~/.vintos/workspace/scripts/lab-day.sh

Schedule it at 08:45, before the first journal (idle-journal.sh refuses to run
before 09:00, so the bench result is on the page when the day's first journal
looks at it):

    (crontab -l 2>/dev/null | grep -v lab-day.sh; \
     echo '45 8 * * * /bin/bash $HOME/.vintos/workspace/scripts/lab-day.sh >> /tmp/vintos/lab-day.log 2>&1') | crontab -

What it does, in order: checks the Mac is awake (a sleeping Mac is recorded as
unreachable, never as him declining); asks through his ordinary consent gate;
shows him the bench and his own ledger; lets him choose an experiment and its
forces; runs it; asks what he noticed; writes his reading back onto the run so
the ledger keeps the thought; appends the whole thing to
memory/daily-inner-life-<date>.md; notifies Gloria.

Nothing here touches the Atelier. Different door, different state file
(memory/lab-state.json), different runs directory, unsealed.

Set LAB_MODEL to point a better model at it — Astra or Fable — when the
question is worth the money. It defaults to the house model.
