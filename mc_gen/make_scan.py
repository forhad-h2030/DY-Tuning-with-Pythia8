#!/usr/bin/env python3
"""Generate the low-mass primordial-kT scan: a Sobol design in the chosen parameters
(default: soft, hard, hs and hm; fewer with e.g. --params soft hard).

  BeamRemnants:primordialKTsoft   soft   0.2 - 1.5   [0.9]
  BeamRemnants:primordialKThard   hard   0.5 - 2.5   [1.8]   (soft <= hard)
  BeamRemnants:halfScaleForKT     hs     0.5 - 4.0   [1.5]
  BeamRemnants:halfMassForKT      hm     0.25 - 3.0  [1.0]

Everything else is left at the Pythia default (SpaceShower:pT0Ref is not set), mHat = 0.25 - 10 GeV.
Point 0 is the Pythia default, kept as an anchor. Writes phpythia8_DY_tune<first>.cfg ...
and scan_design.csv (the design table the fit script reads).

Usage: python3 make_scan.py [--first 1] [--npoints 30] [--params soft hard hs hm] [--seed 1] [--dry-run]
"""
import argparse
import csv
from pathlib import Path

import numpy as np
from scipy.stats import qmc

RANGES = {  # name: (lo, hi, default, Pythia key)
    "soft": (0.2, 1.5, 0.9, "BeamRemnants:primordialKTsoft"),
    "hard": (0.5, 2.5, 1.8, "BeamRemnants:primordialKThard"),
    "hs": (0.5, 4.0, 1.5, "BeamRemnants:halfScaleForKT"),
    "hm": (0.25, 3.0, 1.0, "BeamRemnants:halfMassForKT"),
}
MHAT = (0.25, 10.0)
TEMPLATE = Path(__file__).with_name("phpythia8_DY.cfg")


def design(npoints, seed, names):
    lo = np.array([RANGES[n][0] for n in names])
    hi = np.array([RANGES[n][1] for n in names])
    pts = []
    m = 5
    while len(pts) < npoints - 1:  # soft <= hard by rejection; draw more Sobol points until enough
        u = qmc.Sobol(d=len(names), scramble=True, seed=seed).random_base2(m)
        x = np.round(lo + u * (hi - lo), 3)
        pts = [r for r in x if r[0] <= r[1]]
        m += 1
    pts = pts[: npoints - 1]
    default = [RANGES[n][2] for n in names]
    return names, [default] + [list(map(float, p)) for p in pts]


def write_cfg(path, tune, row, names):
    out = []
    for line in TEMPLATE.read_text().splitlines():
        if line.startswith("PhaseSpace:mHatMin"):
            line = f"PhaseSpace:mHatMin = {MHAT[0]}  ! default = 4.; minimum = 0."
        elif line.startswith("PhaseSpace:mHatMax"):
            line = f"PhaseSpace:mHatMax = {MHAT[1]}  ! default = 4.; minimum = 0."
        elif line.startswith(("! Tune", "BeamRemnants:", "SpaceShower:pT0Ref")):
            continue
        out.append(line)
    while out and not out[-1].strip():
        out.pop()
    out.append(f"! Tune {tune:02d}: low-mass kT scan (Sobol design, only the lines below differ between tunes)")
    for n, v in zip(names, row):
        out.append(f"{RANGES[n][3]} = {v}")
    Path(path).write_text("\n".join(out) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--npoints", type=int, default=30, help="including the default anchor")
    ap.add_argument("--params", nargs="+", default=["soft", "hard", "hs", "hm"], choices=list(RANGES))
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    names, rows = design(args.npoints, args.seed, args.params)
    here = Path(__file__).parent
    print(f"{'tune':<8}" + "".join(f"{n:>8}" for n in names))
    for i, r in enumerate(rows):
        print(f"tune{args.first + i:02d} " + "".join(f"{v:8.3f}" for v in r))
    if args.dry_run:
        return
    for i, r in enumerate(rows):
        write_cfg(here / f"phpythia8_DY_tune{args.first + i:02d}.cfg", args.first + i, r, names)
    with open(here / "scan_design.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["tune"] + names)
        for i, r in enumerate(rows):
            w.writerow([f"tune{args.first + i:02d}"] + r)
    print(f"\nwrote {len(rows)} cfgs and scan_design.csv")


if __name__ == "__main__":
    main()
