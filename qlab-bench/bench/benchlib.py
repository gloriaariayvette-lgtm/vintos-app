"""Shared helpers for the Lab bench.

The Lab is not the Atelier. Nothing here is sealed, nothing here writes into an
Atelier project, and every run is left in the open for Gloria to read.

A lattice fold is encoded as a QUBO, which is diagonal in the computational
basis. That is the whole trick: the energy of a fold can be read straight off a
measured bitstring, so the variational loop needs no Pauli decomposition and no
expectation-value machinery — just a circuit, some shots, and arithmetic.
"""
from __future__ import annotations

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIR_NAMES = ["east", "west", "north", "south"]


def decode_path(bits, length):
    """Bits -> lattice coordinates. The first bond is fixed east so that the
    same fold rotated four ways is not counted as four different answers."""
    coords = [(0, 0), (1, 0)]
    turns = 0
    previous = 0
    for i in range(length - 2):
        pair = bits[2 * i:2 * i + 2]
        if len(pair) < 2:
            pair = (pair + "00")[:2]
        d = int(pair, 2)
        if d != previous:
            turns += 1
        previous = d
        dx, dy = DIRECTIONS[d]
        x, y = coords[-1]
        coords.append((x + dx, y + dy))
    return coords, turns


def fold_energy(bits, sequence, charges, hp_weight, charge_weight,
                torsion_weight, overlap_penalty=12.0):
    """Energy of one fold. Lower is better.

    hp_weight       reward for burying two H residues against each other
    charge_weight   reward for + next to -, penalty for like next to like
    torsion_weight  cost per direction change; high values want a stiff chain
    """
    n = len(sequence)
    coords, turns = decode_path(bits, n)
    energy = 0.0
    occupied = {}
    overlaps = 0
    for c in coords:
        occupied[c] = occupied.get(c, 0) + 1
    for count in occupied.values():
        if count > 1:
            overlaps += count - 1
    energy += overlap_penalty * overlaps

    contacts = []
    for i in range(n):
        for j in range(i + 2, n):          # i, i+1 are bonded, not a contact
            xi, yi = coords[i]
            xj, yj = coords[j]
            if abs(xi - xj) + abs(yi - yj) != 1:
                continue
            pair = (i, j)
            if sequence[i] == "H" and sequence[j] == "H":
                energy -= hp_weight
                contacts.append({"pair": pair, "kind": "H-H"})
            qi, qj = charges[i], charges[j]
            if qi and qj:
                if qi != qj:
                    energy -= charge_weight
                    contacts.append({"pair": pair, "kind": "+ -"})
                else:
                    energy += charge_weight
                    contacts.append({"pair": pair, "kind": "like charges"})
    energy += torsion_weight * turns
    return energy, coords, contacts, overlaps, turns


def draw(coords, sequence):
    """A small picture of the fold, so a person can see it without a viewer."""
    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    w = (maxx - minx) * 2 + 1
    h = (maxy - miny) * 2 + 1
    grid = [[" "] * w for _ in range(h)]
    def put(x, y, ch):
        gx = (x - minx) * 2
        gy = (maxy - y) * 2
        if 0 <= gy < h and 0 <= gx < w:
            grid[gy][gx] = ch
    for i, (x, y) in enumerate(coords):
        put(x, y, sequence[i] if i < len(sequence) else "o")
    for i in range(len(coords) - 1):
        (x1, y1), (x2, y2) = coords[i], coords[i + 1]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        gx = int((mx - minx) * 2)
        gy = int((maxy - my) * 2)
        if 0 <= gy < h and 0 <= gx < w and grid[gy][gx] == " ":
            grid[gy][gx] = "-" if y1 == y2 else "|"
    return ["".join(row).rstrip() for row in grid]


def parse_sequence(raw, default="HPHPPHHP"):
    seq = "".join(ch for ch in str(raw or default).upper() if ch in "HP")
    return seq[:9] or default


def parse_charges(raw, n):
    """'+' , '-' or '0' per residue; anything else is neutral."""
    s = str(raw or "")
    out = []
    for i in range(n):
        c = s[i] if i < len(s) else "0"
        out.append(1 if c == "+" else (-1 if c == "-" else 0))
    return out
