#!/usr/bin/env python3
"""3x3 overlay of a tune and the weighted E906 generator (trigger emulation, unit area): mass, pT, xF, and px, py, pz of mu+ and mu-.
Note figure overlay_grid_root.png. Mean and sigma of both samples are on the pads.
Run: PYTHONPATH=$(root-config --libdir) python3 fig_grid_root.py [--tune tune25]
"""
import argparse

import numpy as np
import ROOT

from final_files import tune_file

ap = argparse.ArgumentParser()
ap.add_argument("--tune", default="tune25")
ap.add_argument("--legacy", default="../data/DY-Legacy-Oct12-2026_Combined.root")
ap.add_argument("--target", default="target_pt_LH2_E906_RS67.csv")
ap.add_argument("--out", default="../../ana_note/figs/overlay_grid_root.png")
args = ap.parse_args()

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

MUON_MASS = 0.1056
M_P, E_BEAM = 0.938272, 120.0  # beam energy of the Pythia cfg (eA = 120)
SQRT_S = np.sqrt(2 * M_P * E_BEAM + 2 * M_P**2)
BETA, GAMMA = np.sqrt(E_BEAM**2 - M_P**2) / (E_BEAM + M_P), (E_BEAM + M_P) / SQRT_S  # boost of the CM frame
COLS = [f"{c}_{s}" for s in ("pos", "neg") for c in ("px", "py", "pz")]  # mu+ px,py,pz then mu- px,py,pz


def read(path, weighted):
    """Quantities of the first triggered reconstructed pair of each event, and the weights."""
    df = ROOT.RDataFrame("tree", path)
    df = df.Filter("rec_dimuon_px_pos_tgt.size() > 0 && rec_dimuon_px_neg_tgt.size() > 0 && evtPassTrigEmu != 0")
    for c in COLS:
        df = df.Define(c, f"rec_dimuon_{c}_tgt[0]")
    df = df.Define("w", "weight" if weighted else "1.0")
    a = df.AsNumpy(COLS + ["w"])
    p = [a[c].astype(np.float64) for c in COLS]
    ep = np.sqrt(p[0]**2 + p[1]**2 + p[2]**2 + MUON_MASS**2)
    en = np.sqrt(p[3]**2 + p[4]**2 + p[5]**2 + MUON_MASS**2)
    px, py, pz, e = p[0] + p[3], p[1] + p[4], p[2] + p[5], ep + en
    print(f"{path}: {len(e)} triggered events with a reconstructed pair")
    return {"mass": np.sqrt(np.maximum(e**2 - px**2 - py**2 - pz**2, 0)), "pt": np.hypot(px, py),
            "xf": 2 * GAMMA * (pz - BETA * e) / SQRT_S, "p": p}, a["w"].astype(np.float64)


def cfg_lines(tune):
    """Active settings of the PYTHIA cfg of a tune (comments and blank lines dropped), as 'key = value'."""
    out = []
    for line in open(f"../phpythia8_DY_{tune}.cfg"):
        line = line.split("!")[0].strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = (s.strip() for s in line.split("=", 1))
            out.append(f"{k} = {v}")
    return out


tune = read(tune_file(args.tune), False)
legacy = read(args.legacy, True)

import csv
rows = list(csv.DictReader(open(args.target)))
data_edges = np.array([float(r["pt_lo"]) for r in rows] + [float(rows[-1]["pt_hi"])])  # nine 0.25 GeV/c bins, 0 to 2.25

panels = [("mass", None, (20, 0, 10), "m_{#mu^{+}#mu^{-}} [GeV/c^{2}]"),
          ("pt", None, data_edges, "p_{T}^{#mu^{+}#mu^{-}} [GeV/c]"),
          ("xf", None, (24, 0, 1.2), "x_{F}")]
rng = {"px": (20, -4, 4), "py": (20, -3, 3), "pz": (20, 0, 100)}
for r, lab in enumerate(("#mu^{+}", "#mu^{-}")):
    for c, comp in enumerate(("px", "py", "pz")):
        panels.append(("p", 3 * r + c, rng[comp], f"{lab} {comp[0]}_{{{comp[1]}}} [GeV/c]"))

BLUE, RED = ROOT.kAzure + 1, ROOT.kRed + 1
canvas = ROOT.TCanvas("c", "", 1500, 1000)
split = 0.80  # the left part holds the 3x3 pads, the right part the legend
keep = []
for k, (key, idx, binning, xtitle) in enumerate(panels):
    row, col = divmod(k, 3)
    pad = ROOT.TPad(f"pad{k}", "", col * split / 3, 1 - (row + 1) / 3, (col + 1) * split / 3, 1 - row / 3)
    pad.SetLeftMargin(0.17); pad.SetRightMargin(0.04); pad.SetTopMargin(0.05); pad.SetBottomMargin(0.15); pad.SetGrid()
    pad.Draw(); pad.cd()
    hs, xs = [], {}
    for name, (d, w) in (("tune", tune), ("legacy", legacy)):
        x = np.ascontiguousarray(d[key] if idx is None else d[key][idx])
        xs[name] = (x, w)
        h = ROOT.TH1D(f"h_{name}_{k}", "", *binning) if isinstance(binning, tuple) else ROOT.TH1D(f"h_{name}_{k}", "", len(binning) - 1, binning)
        h.Sumw2()
        h.FillN(len(x), x, w)
        h.Scale(1.0 / h.Integral())  # unit area ...
        h.Scale(1.0, "width")        # ... as a density; the errors scale with the contents
        hs.append(h)
    ht, hl = hs
    ht.SetLineColor(BLUE); ht.SetLineWidth(2)
    hl.SetLineColor(RED); hl.SetMarkerColor(RED); hl.SetMarkerStyle(20); hl.SetMarkerSize(0.9); hl.SetLineWidth(2)
    hd = None
    if key == "pt":  # E906 hydrogen data on the same pad, contents and errors from the CSV
        hd = ROOT.TH1D(f"h_data_{k}", "", len(binning) - 1, binning)
        hd.Sumw2()
        for i, r in enumerate(rows, start=1):
            hd.SetBinContent(i, float(r["counts"])); hd.SetBinError(i, float(r["err"]))
        hd.Scale(1.0 / hd.Integral()); hd.Scale(1.0, "width")
        hd.SetMarkerStyle(21); hd.SetMarkerColor(ROOT.kBlack); hd.SetLineColor(ROOT.kBlack); hd.SetMarkerSize(0.9)
        hdata_keep = hd
    top = max(ht.GetMaximum(), hl.GetMaximum() + hl.GetBinError(hl.GetMaximumBin()), hd.GetMaximum() if hd else 0)
    ht.SetMinimum(0)
    ht.SetMaximum((1.75 if hd else 1.5) * top)
    ax = ht.GetXaxis(); ay = ht.GetYaxis()
    ax.SetTitle(xtitle); ax.SetTitleSize(0.06); ax.SetLabelSize(0.052); ax.SetTitleOffset(1.0)
    ay.SetTitle("normalized counts"); ay.SetTitleSize(0.06); ay.SetLabelSize(0.052); ay.SetTitleOffset(1.35)
    ay.SetNdivisions(505)
    ht.Draw("HIST")
    hl.Draw("E1 SAME")
    if hd:
        hd.Draw("PE SAME")
    # mean and sigma of both samples (TH1 statistics, weighted for the legacy sample)
    tex = ROOT.TLatex(); tex.SetNDC(); tex.SetTextFont(42); tex.SetTextSize(0.043)
    lines = [(0.89, h.GetMean(), h.GetStdDev(), col, name) for h, col, name in ((ht, BLUE, f"{args.tune} (pythia8)"), (hl, RED, "E906 gen."))]
    if hd:  # pT pad: mean and sigma of the simulations for pT < 2.25 GeV/c (as in the note's table), of the data from its bins
        for name_, (x_, w_) in xs.items():
            m_ = x_ < 2.25
            mean_ = np.average(x_[m_], weights=w_[m_]); sig_ = np.sqrt(np.average((x_[m_] - mean_) ** 2, weights=w_[m_]))
            lines[0 if name_ == "tune" else 1] = (lines[0 if name_ == "tune" else 1][0], mean_, sig_) + lines[0 if name_ == "tune" else 1][3:]
        lines.append((0.75, hd.GetMean(), hd.GetStdDev(), ROOT.kBlack, "E906 data"))
    for n_, (y, mean_, sig_, col, name) in enumerate(lines):
        tex.SetTextColor(col)
        tex.DrawLatex(0.20, 0.89 - 0.075 * n_, f"{name}: mean {mean_:.3g}, #sigma {sig_:.3g}")
    keep += [pad, ht, hl, tex] + ([hd] if hd else [])
    if hd: pt_data_hist = hd
    canvas.cd()

# legend in the right column
canvas.cd()
leg = ROOT.TLegend(split + 0.01, 0.82, 0.995, 0.96); leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextSize(0.019)
leg.AddEntry(keep[1], f"{args.tune} (pythia8)", "l")
leg.AddEntry(keep[2], "E906 generator (weighted)", "pe")
leg.AddEntry(pt_data_hist, "E906 LH2 data", "pe")
leg.Draw()

canvas.SaveAs(args.out)
print("wrote", args.out)
