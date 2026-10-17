#!/usr/bin/env python3
"""Primordial-kT width against dimuon mass (soft and hard parts) for the default, fitted and chosen settings; E/m from the reconstructed pairs of the chosen tune.
Not in the note. Run: python3 fig_sigma_kt.py [--tune tune25] [--out sigma_kt.png]
"""
import argparse
import csv

import awkward as ak
import matplotlib.pyplot as plt
import numpy as np
import uproot

from final_files import tune_file
from pt_vs_config import BRANCHES, MUON_MASS, TRIG

ap = argparse.ArgumentParser()
ap.add_argument("--tune", default="tune25")
ap.add_argument("--out", default="sigma_kt.png")
args = ap.parse_args()

M_P, E_BEAM, R_RED = 0.938272, 120.0, 0.5
SQRT_S = np.sqrt(2 * M_P * E_BEAM + 2 * M_P**2)
BETA, GAMMA = np.sqrt(E_BEAM**2 - M_P**2) / (E_BEAM + M_P), (E_BEAM + M_P) / SQRT_S

# E/m of the pair in the CM frame, per mass bin, from the reconstructed triggered pairs of the chosen tune
a = uproot.open(tune_file(args.tune))["tree"].arrays(BRANCHES + [TRIG], library="ak")
a = a[(ak.num(a[BRANCHES[0]]) > 0) & (ak.num(a[BRANCHES[3]]) > 0) & (a[TRIG] != 0)]
p = [ak.to_numpy(ak.firsts(a[b])) for b in BRANCHES]
e = np.sqrt(p[0]**2 + p[1]**2 + p[2]**2 + MUON_MASS**2) + np.sqrt(p[3]**2 + p[4]**2 + p[5]**2 + MUON_MASS**2)
px, py, pz = p[0] + p[3], p[1] + p[4], p[2] + p[5]
mass = np.sqrt(np.maximum(e**2 - px**2 - py**2 - pz**2, 0))
e_cm = GAMMA * (e - BETA * pz)
edges = np.arange(1.0, 9.01, 0.5)
mid = 0.5 * (edges[1:] + edges[:-1])
ydamp = np.array([np.median((e_cm[(mass >= lo) & (mass < hi)] / mass[(mass >= lo) & (mass < hi)]) ** R_RED)
                  if ((mass >= lo) & (mass < hi)).sum() > 20 else np.nan for lo, hi in zip(edges[:-1], edges[1:])])
ok = np.isfinite(ydamp)
yd = lambda m: np.interp(m, mid[ok], ydamp[ok])
print("y_damp by mass bin:", dict(zip(np.round(mid[ok], 2), np.round(ydamp[ok], 2))))


def parts(m, s, h, hs, hm):
    f = m / (m + hm * yd(m))
    return s * hs / (hs + m) * f, h * m / (hs + m) * f  # soft part, hard part


design = {r["tune"]: r for r in csv.DictReader(open("../scan_design.csv"))}
t = design[args.tune]
sets = [("PYTHIA default", (0.9, 1.8, 1.5, 1.0)),
        ("fit minimum", (0.869, 0.899, 0.635, 1.138)),
        (f"{args.tune} (pythia8)", tuple(float(t[k]) for k in ("soft", "hard", "hs", "hm")))]
m = np.linspace(1.0, 8.0, 200)

fig, ax = plt.subplots(1, 3, figsize=(11, 3.1), sharey=True)
for a_, (name, v) in zip(ax, sets):
    so, ha = parts(m, *v)
    a_.stackplot(m, so, ha, colors=["#9ecae1", "#e6550d"], alpha=0.85, labels=["soft part", "hard part"])
    a_.plot(m, so + ha, color="k", lw=1.2)
    a2 = a_.twinx()
    a2.hist(mass, bins=np.arange(1.0, 9.01, 0.5), histtype="step", color="0.25", lw=1.2, ls="--", density=True)
    a2.set_yticks([])
    a2.set_ylim(0, a2.get_ylim()[1] * 1.45)
    a_.set_ylim(0, 1.7)
    a_.set_title(f"{name}: soft {v[0]:.3g}, hard {v[1]:.3g}, hs {v[2]:.3g}, hm {v[3]:.3g}", fontsize=8)
    a_.set_xlabel(r"dimuon mass $m$ [GeV/$c^2$]")
    a_.grid(alpha=0.3)
    a_.set_xlim(1, 8)
ax[0].set_ylabel(r"$\sigma(m)$ per parton [GeV]")
ax[0].plot([], [], color="0.25", ls="--", lw=1.2, label="reco mass (arb.)")
ax[0].legend(frameon=False, fontsize=8, loc="upper left")
for name, v in sets:
    so, ha = parts(np.array([1.5, 3.0, 6.0]), *v)
    print(f"{name:<22} sigma(1.5, 3, 6 GeV) = " + ", ".join(f"{a:.2f}" for a in so + ha) + "   soft share = " + ", ".join(f"{100*a/(a+b):.0f}%" for a, b in zip(so, ha)))
fig.tight_layout(pad=0.5)
fig.savefig(args.out, dpi=150)
print("wrote", args.out)
