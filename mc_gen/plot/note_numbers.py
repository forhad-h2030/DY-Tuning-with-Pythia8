#!/usr/bin/env python3
"""Numbers quoted in the note for tune01, tune25, tune29 and the E906 generator: chi2 and mean/sigma of pT against the data,
mass fractions, smoothness of the mass spectrum, mean pair pT against mass. Run: python3 note_numbers.py
"""
import csv

import awkward as ak
import numpy as np
import uproot
from scipy.optimize import curve_fit

from pt_vs_config import BRANCHES, MUON_MASS, pair_pt_mass, tune_file

TARGET = "target_pt_LH2_E906_RS67.csv"
EDGES = np.arange(0, 2.5001, 0.25)

rows = list(csv.DictReader(open(TARGET)))
lo = np.array([float(r["pt_lo"]) for r in rows]); hi = np.array([float(r["pt_hi"]) for r in rows])
cnt = np.array([float(r["counts"]) for r in rows]); err = np.array([float(r["err"]) for r in rows])
nb = len(rows)                      # bins used (the last one has no entries and is dropped)
d, dd = cnt / cnt.sum() / 0.25, err / cnt.sum() / 0.25
print(f"data: {nb} bins, sum of weights {cnt.sum():.0f}")


def shape(pt, w=None):
    h, _ = np.histogram(pt, bins=EDGES[:nb + 1], weights=w)
    h2, _ = np.histogram(pt, bins=EDGES[:nb + 1], weights=None if w is None else w**2)
    tot = h.sum()
    return h / tot / 0.25, np.sqrt(h2 if w is not None else h) / tot / 0.25


def legacy(path):
    return pair_pt_mass(uproot.open(path + ":tree"), True, with_weight=True)


samples = {}
for t in ("tune01", "tune25", "tune29"):
    with uproot.open(tune_file(t)) as f:
        pt, m = pair_pt_mass(f["tree"], True)
    samples[t] = (pt, m, None)
samples["legacy"] = legacy("../data/DY-Legacy-Oct12-2026_Combined.root")

print("\nname      N(reco)  mean pT  sigma pT   chi2/ndf vs data (pT<2.25)")
print(f"{'data':<9}{'':>8}  0.718    0.390")
for name, (pt, m, w) in samples.items():
    s = pt < 2.25
    mean = np.average(pt[s], weights=None if w is None else w[s])
    sig = np.sqrt(np.average((pt[s] - mean)**2, weights=None if w is None else w[s]))
    f, df = shape(pt, w)
    chi2 = np.sum((f - d)**2 / (df**2 + dd**2))
    print(f"{name:<9}{len(pt):8d}  {mean:.3f}   {sig:.3f}     {chi2:.1f}/{nb}")

print("\nmass fractions (reco)   <1.5   1.5-2.5   2.5-4.2   >4.2    mean mass")
for name, (pt, m, w) in samples.items():
    ww = np.ones_like(m) if w is None else w
    fr = [ww[(m >= a) & (m < b)].sum() / ww.sum() for a, b in [(0, 1.5), (1.5, 2.5), (2.5, 4.2), (4.2, 99)]]
    print(f"{name:<22}" + "  ".join(f"{100 * x:5.1f}%" for x in fr) + f"    {np.average(m, weights=ww):.2f}")

print("\nsmoothness of the reco mass spectrum, 0.25 GeV bins, fit of a * m^b * exp(-c m) between 1.5 and 7 GeV")
for name in ("tune01", "tune25"):
    m = samples[name][1]
    h, e = np.histogram(m, bins=np.arange(1.5, 7.01, 0.25)); x = 0.5 * (e[1:] + e[:-1])
    p, _ = curve_fit(lambda x, a, b, c: a * x**b * np.exp(-c * x), x, h, p0=[100, 2, 0.5], sigma=np.sqrt(np.maximum(h, 1)), maxfev=20000)
    chi2 = np.sum((h - p[0] * x**p[1] * np.exp(-p[2] * x))**2 / np.maximum(h, 1))
    print(f"{name}: chi2/ndf = {chi2:.1f}/{len(h) - 3}, bins with fewer than 5 entries: {int((h < 5).sum())}")

print("\nfull-simulation mean reco pair pT against mass (GeV/c), tune01 (default) and tune25")
for a, b in [(1.5, 2), (2, 3), (3, 4), (4, 6)]:
    out = []
    for name in ("tune01", "tune25"):
        pt, m, _ = samples[name]; s = (m >= a) & (m < b); out.append(f"{name} {pt[s].mean():.2f} (N={s.sum()})")
    print(f"{a}-{b}: " + ",  ".join(out))
