#!/usr/bin/env python3
"""Dimuon pT overlay with sim/data ratio: E906 LH2 data, PYTHIA tunes, weighted E906 generator (trigger emulation, unit area).
Note figure overlay_pt_main.png. Errors: Sumw2 for the simulations, CSV errors for the data.
Run: PYTHONPATH=$(root-config --libdir) python3 overlay_pt_root.py --tunes tune25 tune01 --no-box --out ../../ana_note/figs/overlay_pt_main.png
"""
import argparse
import csv

import numpy as np
import ROOT

from final_files import tune_file

ap = argparse.ArgumentParser()
ap.add_argument("--tunes", nargs="+", default=["tune25"])
ap.add_argument("--target", default="target_pt_LH2_E906_RS67.csv")
ap.add_argument("--legacy", default="../data/DY-Legacy-Oct12-2026_Combined.root")
ap.add_argument("--label", default="E906 LH2 data")
ap.add_argument("--no-box", action="store_true")
ap.add_argument("--out", default="overlay_pt_root.png")
args = ap.parse_args()

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)

# first reconstructed mu+ mu- pair of each triggered event, pair pT at the target
ROOT.gInterpreter.Declare("""
template <typename T> double pair_pt(const ROOT::VecOps::RVec<T>& pxp, const ROOT::VecOps::RVec<T>& pyp,
                                     const ROOT::VecOps::RVec<T>& pxn, const ROOT::VecOps::RVec<T>& pyn) {
    return std::hypot(pxp[0] + pxn[0], pyp[0] + pyn[0]);
}
""")


def read_pt(path, weighted):
    """pT and weight arrays of the selected events (weight = 1 for an unweighted sample)."""
    df = ROOT.RDataFrame("tree", path)
    df = (df.Filter("rec_dimuon_px_pos_tgt.size() > 0 && rec_dimuon_px_neg_tgt.size() > 0 && evtPassTrigEmu != 0")
            .Define("pt", "pair_pt(rec_dimuon_px_pos_tgt, rec_dimuon_py_pos_tgt, rec_dimuon_px_neg_tgt, rec_dimuon_py_neg_tgt)")
            .Define("w", "weight" if weighted else "1.0"))
    a = df.AsNumpy(["pt", "w"])
    print(f"{path}: {len(a['pt'])} triggered events with a reconstructed pair")
    return a["pt"].astype(np.float64), a["w"].astype(np.float64)


def unit_area(h):
    """Unit area and per-GeV/c density; the bin errors scale with the contents."""
    h.Scale(1.0 / h.Integral())
    h.Scale(1.0, "width")
    return h


rows = list(csv.DictReader(open(args.target)))
edges = np.array([float(r["pt_lo"]) for r in rows] + [float(rows[-1]["pt_hi"])])
n = len(rows)

# data: contents and errors from the CSV
hdata = ROOT.TH1D("hdata", "", n, edges)
hdata.Sumw2()
for i, r in enumerate(rows, start=1):
    hdata.SetBinContent(i, float(r["counts"]))
    hdata.SetBinError(i, float(r["err"]))
mean_data = np.average(0.5 * (edges[1:] + edges[:-1]), weights=[float(r["counts"]) for r in rows])
unit_area(hdata)

def cfg_lines(tune):
    """Active settings of the PYTHIA cfg of a tune (comments and blank lines dropped), as 'key = value'."""
    out = []
    for line in open(f"../phpythia8_DY_{tune}.cfg"):
        line = line.split("!")[0].strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = (s.strip() for s in line.split("=", 1))
            out.append(f"{k} = {v}")
    return out


colors = [ROOT.kAzure + 1, ROOT.kOrange + 1, ROOT.kGreen + 2]
sims = []  # (histogram, legend text, draw option, color, marker style)
for i, t in enumerate(args.tunes):
    pt, w = read_pt(tune_file(t), False)
    h = ROOT.TH1D(f"h_{t}", "", n, edges)
    h.Sumw2()
    h.FillN(len(pt), pt, w)
    sims.append((unit_area(h), f"{t} (pythia8), mean {pt[pt < 2.25].mean():.2f}", "HIST SAME", colors[i], 0))
pt, w = read_pt(args.legacy, True)
hl = ROOT.TH1D("h_legacy", "", n, edges)
hl.Sumw2()
hl.FillN(len(pt), pt, w)
sims.append((unit_area(hl), f"E906 legacy generator, weighted (mean {np.average(pt[pt < 2.25], weights=w[pt < 2.25]):.2f})",
             "HIST SAME", ROOT.kRed + 1, 20))

# ---- canvas: spectrum on top, sim / data below
c = ROOT.TCanvas("c", "", 800, 700) if args.no_box else ROOT.TCanvas("c", "", 1100, 560)
c.SetFillColor(0); c.SetFillStyle(1001)
top = ROOT.TPad("top", "", 0, 0.30, 1, 1); top.SetBottomMargin(0.02); top.SetRightMargin(0.04 if args.no_box else 0.36); top.SetGrid(); top.SetFillColor(0); top.SetFillStyle(1001); top.SetFrameFillColor(0); top.Draw()
bot = ROOT.TPad("bot", "", 0, 0, 1, 0.30); bot.SetTopMargin(0.03); bot.SetBottomMargin(0.36); bot.SetRightMargin(0.04 if args.no_box else 0.36); bot.SetGrid(); bot.SetFillColor(0); bot.SetFillStyle(1001); bot.SetFrameFillColor(0); bot.Draw()

if args.no_box:
    top.SetLeftMargin(0.12); bot.SetLeftMargin(0.12); top.SetTopMargin(0.03); top.SetRightMargin(0.03); bot.SetRightMargin(0.03)
top.cd()
hdata.SetMarkerStyle(20); hdata.SetMarkerColor(ROOT.kBlack); hdata.SetLineColor(ROOT.kBlack)
hdata.GetXaxis().SetLabelSize(0)
hdata.GetYaxis().SetTitle("normalized entries / (GeV/c)")
hdata.GetYaxis().SetTitleSize(0.05); hdata.GetYaxis().SetLabelSize(0.045); hdata.GetYaxis().SetTitleOffset(0.9)
hdata.SetMaximum(1.15 * max(hdata.GetMaximum(), *(h.GetMaximum() for h, *_ in sims)))
hdata.SetMinimum(0)
hdata.Draw("PE")
leg = ROOT.TLegend(0.50, 0.72, 0.97, 0.94) if args.no_box else ROOT.TLegend(0.30, 0.74, 0.62, 0.92); leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextSize(0.035)
leg.AddEntry(hdata, f"{args.label} (mean {mean_data:.2f})", "pe")
for h, text, opt, col, mk in sims:
    h.SetLineColor(col); h.SetLineWidth(2)
    if mk:
        h.SetMarkerStyle(mk); h.SetMarkerColor(col); h.SetMarkerSize(0.9)
    h.Draw(opt)
    leg.AddEntry(h, text, "pe" if mk else "l")
hdata.Draw("PE SAME")
leg.Draw()
# full PYTHIA config of the first tune, as written in its cfg file
c.cd()
box = ROOT.TPaveText(0.69, 0.40, 0.99, 0.92, "NDC"); box.SetBorderSize(0); box.SetFillStyle(0)
box.SetTextAlign(12); box.SetTextFont(42); box.SetTextSize(0.030)
box.AddText(f"phpythia8_DY_{args.tunes[0]}.cfg:")
for ln in cfg_lines(args.tunes[0]):
    box.AddText(ln)
if not args.no_box:
    box.Draw()

bot.cd()
# band: the relative error of the data around 1
band = hdata.Clone("band")
for i in range(1, n + 1):
    band.SetBinError(i, hdata.GetBinError(i) / hdata.GetBinContent(i))
    band.SetBinContent(i, 1.0)
band.SetFillColor(ROOT.kGray + 1); band.SetFillStyle(3001); band.SetLineColor(ROOT.kGray + 1); band.SetMarkerSize(0)
band.GetYaxis().SetRangeUser(0.2, 1.8); band.GetYaxis().SetNdivisions(505)
band.GetYaxis().SetTitle("sim / data"); band.GetYaxis().SetTitleSize(0.13); band.GetYaxis().SetLabelSize(0.11); band.GetYaxis().SetTitleOffset(0.38)
band.GetXaxis().SetTitle("p_{T}^{#mu^{+}#mu^{-}} [GeV/c]")
band.GetXaxis().SetTitleSize(0.14); band.GetXaxis().SetLabelSize(0.11); band.GetXaxis().SetTitleOffset(1.0)
band.Draw("E2")
ratios = []
for h, text, opt, col, mk in sims:
    r = h.Clone(h.GetName() + "_ratio")
    r.Divide(hdata)
    # The data uncertainty is shown by the grey band; show the simulation uncertainty here only.
    for ibin in range(1, n + 1):
        r.SetBinError(ibin, h.GetBinError(ibin) / hdata.GetBinContent(ibin))
    r.SetMarkerStyle(1)
    r.SetMarkerColor(col)
    r.SetLineColor(col)
    ratios.append(r)
    r.Draw("HIST SAME")
    r.Draw("E1 SAME")
line = ROOT.TLine(edges[0], 1, edges[-1], 1); line.Draw()

c.SaveAs(args.out)
print("wrote", args.out)
