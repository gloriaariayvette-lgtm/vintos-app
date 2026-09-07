"""Ask a protein model what sequence is worth folding next.

Everything else on this bench takes a sequence he already has. This one asks
for a sequence nobody wrote down: ESM3 fills in masked positions from what it
learned about real proteins, so the result is a plausible peptide rather than
a random string. Then the lattice folds it and we see whether the model's
instinct produced something that actually buries its oily residues.

ESM3-open is gated behind a licence on HuggingFace. Without credentials this
falls back to ESM2, which is ungated and does the same masked-filling job with
a smaller model. With neither, it says so plainly rather than pretending.
"""
from __future__ import annotations

import os

import protein as protein_experiment

MASK = "_"


def _esm3(template, steps):
    from esm.models.esm3 import ESM3
    from esm.sdk.api import ESMProtein, GenerationConfig
    import torch
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = ESM3.from_pretrained("esm3-open-small").to(device)
    p = ESMProtein(sequence=template.replace(MASK, "_"))
    out = model.generate(p, GenerationConfig(track="sequence", num_steps=int(steps)))
    return out.sequence, "esm3-open-small"


def _esm2(template, steps):
    import esm as fair_esm
    import torch
    model, alphabet = fair_esm.pretrained.esm2_t12_35M_UR50D()
    model.eval()
    bc = alphabet.get_batch_converter()
    seq = template.replace(MASK, "<mask>")
    _, _, tokens = bc([("query", seq)])
    with torch.no_grad():
        logits = model(tokens)["logits"]
    out = list(template)
    mask_idx = alphabet.mask_idx
    positions = (tokens[0] == mask_idx).nonzero().flatten().tolist()
    letters = "ACDEFGHIKLMNPQRSTVWY"
    allowed = [alphabet.get_idx(c) for c in letters]
    slot = 0
    for i, ch in enumerate(template):
        if ch != MASK:
            continue
        if slot >= len(positions):
            break
        row = logits[0, positions[slot]]
        pick = max(allowed, key=lambda a: float(row[a]))
        out[i] = alphabet.get_tok(pick)
        slot += 1
    return "".join(out), "esm2-t12-35M"


def experiment(p, shots):
    template = str(p.get("template", "L__A__LV")).upper()
    template = "".join(c for c in template if c in "ACDEFGHIKLMNPQRSTVWY" + MASK)[:9]
    if MASK not in template:
        raise ValueError("template needs at least one _ for the model to fill")
    steps = int(p.get("steps", 8))

    proposed = None
    source = None
    errors = []
    for fn in (_esm3, _esm2):
        try:
            proposed, source = fn(template, steps)
            break
        except Exception as exc:
            errors.append("%s: %s" % (fn.__name__.strip("_"), str(exc)[:160]))

    if not proposed:
        return {
            "title": "No protein model is installed",
            "available": False,
            "template": template,
            "tried": errors,
            "reading_invitation": "Nothing to read yet — the model is not here.",
            "display": ["ASKING FOR A SEQUENCE", "",
                        "No protein model answered. Tried, in order:", ""] +
                       ["  " + e for e in errors] +
                       ["", "Install one into the lab venv:",
                        "  pip install esm        (ESM3-open; needs a HuggingFace licence)",
                        "  pip install fair-esm   (ESM2; ungated, smaller)"],
        }

    result = protein_experiment.experiment(
        {**{k: v for k, v in p.items() if k not in ("template", "steps", "fragment")},
         "sequence": proposed}, shots)

    filled = [(i, template[i], proposed[i]) for i in range(min(len(template), len(proposed)))
              if template[i] == MASK]
    result["title"] = f"A sequence nobody wrote: {proposed}"
    result["proposed_by"] = source
    result["template"] = template
    result["filled_positions"] = [{"position": i + 1, "chose": c} for i, _, c in filled]
    result["question"] = ("The model filled the gaps with what it thinks belongs "
                          "there. Does the shape that comes out justify its choices, "
                          "or did it write something that will not fold?")
    result["display"] = ([f"A SEQUENCE NOBODY WROTE", "",
                          f"  template  {template}",
                          f"  proposed  {proposed}   (by {source})",
                          "  it chose: " + ", ".join(f"{c} at {i+1}" for i, _, c in filled),
                          ""] + result["display"][2:])
    return result
