#!/usr/bin/env python3
"""Reco overlays of the generators, without and with trigger emulator (+ E906 LH2 pT data).
Run: PYTHONPATH=$(root-config --libdir) python3.14 overlay_generators.py

Branches read (tree "tree", first reco pair [0]):
  rec_dimuon_mass_tgt                 dimuon mass
  rec_dimuon_{px,py,pz}_pos_tgt       mu+ momentum at target
  rec_dimuon_{px,py,pz}_neg_tgt       mu- momentum at target (pT, xF from mu+ + mu-)
  evtPassTrigEmu                      trigger emulator (== 1)
  weight, ptReWeight                  legacy event weight
TSSA file:
  mass, rec_dimu_mu_{pos,neg}_{px,py,pz}
LH2 data (csv): pt_lo, pt_hi, counts, err
"""
import numpy as np
import ROOT
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LEGACY = "../data/DY-Legacy-Pt-reweight.root"
TSSA = "../data/DY_ana_raw_100k.root"
DATA = "target_pt_LH2_E906_RS67.csv"   # E906 LH2 pT data
DATA_EDGES = np.arange(0, 2.26, 0.25)   # data binning
OUT = "../slides/figs/overlay_generators_grid"

# label, file, weight, color, line width (0 = points)
SAMPLES = [
    ("PYTHIA8 default", "../data/MC-DY-pythia8-default.root", "1.0", "#2a6fdb", 2.5),
    (r"PYTHIA8 tune25: default PDF, $k_T$ tuned to E906 LH2 $p_T$", "../data/DY-Config-25-Oct12-2026.root", "1.0", "#7b3fb5", 2.5),
    (r"PYTHIA8 production (tune38): CT10nlo, $Q^2=\hat{s}$, $k_T$ crude matching", "../data/DY_tune38.root", "1.0", "#d9631e", 2.5),
    (r"E906 legacy (weight$\times$ptReWeight)", LEGACY, "weight*ptReWeight", "#222222", 0),
]

MUON_MASS = 0.1056
M_P, E_BEAM = 0.938272, 120.0
SQRT_S = np.sqrt(2 * M_P * E_BEAM + 2 * M_P**2)
BETA = np.sqrt(E_BEAM**2 - M_P**2) / (E_BEAM + M_P)
GAMMA = (E_BEAM + M_P) / SQRT_S

PANELS = [
    (r"$m_{\mu^+\mu^-}$ [GeV/$c^2$]", np.linspace(0, 10, 21)),
    (r"$p_T^{\mu\mu}$ [GeV/$c$]", np.linspace(0, 2.5, 21)),
    (r"$x_F$", np.linspace(0, 1.2, 25)),
    (r"$\mu^+$ $p_x$ [GeV/$c$]", np.linspace(-4, 4, 21)),
    (r"$\mu^+$ $p_y$ [GeV/$c$]", np.linspace(-3, 3, 21)),
    (r"$\mu^+$ $p_z$ [GeV/$c$]", np.linspace(0, 100, 21)),
    (r"$\mu^-$ $p_x$ [GeV/$c$]", np.linspace(-4, 4, 21)),
    (r"$\mu^-$ $p_y$ [GeV/$c$]", np.linspace(-3, 3, 21)),
    (r"$\mu^-$ $p_z$ [GeV/$c$]", np.linspace(0, 100, 21)),
]


def nine(mass, p):
    e = np.sqrt(p[0]**2 + p[1]**2 + p[2]**2 + MUON_MASS**2) + np.sqrt(p[3]**2 + p[4]**2 + p[5]**2 + MUON_MASS**2)
    px, py, pz = p[0] + p[3], p[1] + p[4], p[2] + p[5]
    pz_cm = GAMMA * (pz - BETA * e)
    xf = 2 * pz_cm / SQRT_S / (1 - mass**2 / SQRT_S**2)
    return [mass, np.hypot(px, py), xf] + p


def read(path, weight, trig):
    cut = "rec_dimuon_px_pos_tgt.size() > 0 && rec_dimuon_px_neg_tgt.size() > 0"
    if trig:
        cut += " && evtPassTrigEmu == 1"
    df = ROOT.RDataFrame("tree", path).Filter(cut).Define("w", weight)
    cols = [f"{c}_{s}" for s in ("pos", "neg") for c in ("px", "py", "pz")]
    for c in cols:
        df = df.Define(c, f"rec_dimuon_{c}_tgt[0]")
    df = df.Define("mass", "rec_dimuon_mass_tgt[0]")
    a = df.AsNumpy(cols + ["mass", "w"])
    return nine(a["mass"].astype(float), [a[c].astype(float) for c in cols]), a["w"].astype(float)


def read_tssa(path):
    cols = [f"rec_dimu_mu_{s}_{c}" for s in ("pos", "neg") for c in ("px", "py", "pz")]
    a = ROOT.RDataFrame("tree", path).AsNumpy(cols + ["mass"])
    q = nine(a["mass"].astype(float), [a[c].astype(float) for c in cols])
    return q, np.ones(len(q[0]))


def draw(trig):
    samples = [(label, read(path, weight, trig), color, lw) for label, path, weight, color, lw in SAMPLES]
    if not trig:
        samples.append(("TSSA (past) analysis", read_tssa(TSSA), "#2a9d5b", 0))

    fig, axs = plt.subplots(3, 3, figsize=(14, 11))
    for k, (xlabel, edges) in enumerate(PANELS):
        ax = axs.flat[k]
        if trig and k == 1:
            edges = DATA_EDGES
        centers = 0.5 * (edges[1:] + edges[:-1])
        for i, (label, (q, w), color, lw) in enumerate(samples):
            inside = (q[k] >= edges[0]) & (q[k] < edges[-1])
            x, wx = q[k][inside], w[inside]
            norm = wx.sum() * np.diff(edges)
            y = np.histogram(x, edges, weights=wx)[0] / norm
            err = np.sqrt(np.histogram(x, edges, weights=wx**2)[0]) / norm
            if lw == 0:
                ax.errorbar(centers, y, err, xerr=0.5 * np.diff(edges), fmt="o", ms=3.5, color=color, label=label)
            else:
                ax.step(edges, np.append(y, y[-1]), where="post", color=color, lw=lw, label=label)
                ax.errorbar(centers, y, err, fmt="none", ecolor=color, elinewidth=1)
            mean = np.average(x, weights=wx)
            sigma = np.sqrt(np.average((x - mean)**2, weights=wx))
            ax.text(0.03, 0.975 - 0.058 * i, rf"mean {mean:.3g}, $\sigma$ {sigma:.3g}",
                    transform=ax.transAxes, va="top", fontsize=8.5, color=color)
        if trig and k == 1:
            d = np.genfromtxt(DATA, delimiter=",", names=True)
            n, e = d["counts"], d["err"]
            c = 0.5 * (d["pt_lo"] + d["pt_hi"])
            norm = n.sum() * (d["pt_hi"] - d["pt_lo"])
            ax.errorbar(c, n / norm, e / norm, xerr=0.5 * (d["pt_hi"] - d["pt_lo"]), fmt="s", ms=8,
                        color="#d000d0", mec="k", mew=0.8, elinewidth=2.2, capsize=3, capthick=2, zorder=10,
                        label="SeaQuest (E906) LH2 data, roadset 67")
            mean = np.average(c, weights=n)
            sigma = np.sqrt(np.average((c - mean)**2, weights=n))
            ax.text(0.03, 0.975 - 0.058 * len(samples), rf"mean {mean:.3g}, $\sigma$ {sigma:.3g}",
                    transform=ax.transAxes, va="top", fontsize=9.5, color="#d000d0", fontweight="bold")
            print(f"  E906 LH2 data: <pT> {mean:.3f}  sigma {sigma:.3f}  (bin centres)")
        ax.set_xlabel(xlabel, fontsize=15)
        ax.set_ylabel("normalized entries / bin width", fontsize=13)
        ax.tick_params(labelsize=12)
        ax.set_xlim(edges[0], edges[-1])
        ax.set_ylim(0, 1.9 * ax.get_ylim()[1])
        ax.grid(color="#e5e7eb")

    handles, labels = axs[0, 1].get_legend_handles_labels()
    title = "with trigger emulator" if trig else "without trigger emulator"
    leg = fig.legend(handles, labels, title=title, frameon=False, fontsize=10, loc="upper center", ncol=3, columnspacing=1.5)
    for t in leg.get_texts():
        if t.get_text().startswith("SeaQuest"):
            t.set_color("#d000d0"); t.set_fontweight("bold")
    fig.tight_layout(rect=(0, 0, 1, 0.905))
    out = OUT + ("_trig" if trig else "") + ".png"
    fig.savefig(out, dpi=200)
    print("saved", out)
draw(trig=False)
draw(trig=True)
