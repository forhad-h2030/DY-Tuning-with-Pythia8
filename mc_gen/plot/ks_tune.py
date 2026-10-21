#!/usr/bin/env python3
"""KS distance D = max_k |G_k - F_k| of the simulated pT to the E906 LH2 pT histogram (nine bins), errors from 500 replicas.
rank: ranking of the scan files (note tables); plot: cumulative distributions (note figure ks_cdf.png).
Run (ROOT python): ks_tune.py rank | ks_tune.py plot --tunes tune01 tune29 tune25 --out ../../ana_note/figs/ks_cdf.png
"""
import argparse
import csv

import numpy as np
import ROOT

from final_files import tune_file

TARGET = "target_pt_LH2_E906_RS67.csv"
LEGACY = "../data/DY-Legacy-Oct12-2026_Combined.root"
N_REPLICAS = 500

def load_data(path=TARGET):
    rows = list(csv.DictReader(open(path)))
    edges = np.array([float(r["pt_lo"]) for r in rows] + [float(rows[-1]["pt_hi"])])
    return edges, np.array([float(r["counts"]) for r in rows]), np.array([float(r["err"]) for r in rows])

def read_pt(path, weighted=False):
    df = ROOT.RDataFrame("tree", path).Filter(
        "rec_dimuon_px_pos_tgt.size()>0 && rec_dimuon_px_neg_tgt.size()>0 && evtPassTrigEmu!=0")
    df = df.Define("pt", "hypot(rec_dimuon_px_pos_tgt[0]+rec_dimuon_px_neg_tgt[0], rec_dimuon_py_pos_tgt[0]+rec_dimuon_py_neg_tgt[0])")
    df = df.Define("w", "weight" if weighted else "1.0")
    a = df.AsNumpy(["pt", "w"])
    return a["pt"].astype(float), a["w"].astype(float)

def cumulative(contents):
    return np.concatenate([[0.0], np.cumsum(contents / contents.sum())])

def sim_cdf(pt, w, edges):
    return cumulative(np.histogram(pt, edges, weights=w)[0])

def ks_distance(cdf_sim, cdf_data):
    return np.abs(cdf_sim - cdf_data).max()

def data_replicas(N, dN, n=N_REPLICAS, seed=1):
    rng = np.random.default_rng(seed)
    return np.array([cumulative(np.clip(rng.normal(N, dN), 1e-9, None)) for _ in range(n)])

def sim_replicas(pt, w, edges, n=N_REPLICAS, seed=2):
    rng = np.random.default_rng(seed)
    p = w / w.sum() if w.std() > 0 else None
    out = []
    for _ in range(n):
        i = rng.choice(len(pt), len(pt), p=p)
        out.append(cumulative(np.histogram(pt[i], edges)[0].astype(float)))
    return np.array(out)

def ks_error(sim_reps, data_reps, cdf_sim, cdf_data, source="both"):
    if source == "data":
        d = [ks_distance(cdf_sim, r) for r in data_reps]
    elif source == "sim":
        d = [ks_distance(r, cdf_data) for r in sim_reps]
    else:
        d = [ks_distance(s, r) for s, r in zip(sim_reps, data_reps)]
    return np.std(d)

def compare(pt, w, edges, cdf_data, data_reps):
    keep = pt < edges[-1]
    cdf = sim_cdf(pt[keep], w[keep], edges)
    reps = sim_replicas(pt[keep], w[keep], edges)
    m = pt < edges[-1]
    mean = np.average(pt[m], weights=w[m])
    return {"D": ks_distance(cdf, cdf_data), "cdf": cdf, "mean": mean, "sigma": np.sqrt(np.average((pt[m] - mean) ** 2, weights=w[m])),
            "neff": w.sum() ** 2 / (w**2).sum(),
            "err": {s: ks_error(reps, data_reps, cdf, cdf_data, s) for s in ("data", "sim", "both")}}

def rank():
    edges, N, dN = load_data()
    cdf_data, data_reps = cumulative(N), data_replicas(N, dN)
    design = {r["tune"]: r for r in csv.DictReader(open("../scan_design.csv"))}
    res = {t: compare(*read_pt(f"../data/DY_{t}.root"), edges, cdf_data, data_reps) for t in design}
    order = sorted(design, key=lambda t: res[t]["D"])
    print("rank  tune     D      err(data) err(sim) err(both)  <pT>  sigma  Neff   soft   hard   hs     hm    |dmean|+|dsigma| (data 0.718, 0.390)")
    for i, t in enumerate(order, 1):
        r, p = res[t], design[t]
        print(f"{i:>3}   {t}  {r['D']:.4f}  {r['err']['data']:.4f}    {r['err']['sim']:.4f}   {r['err']['both']:.4f}    {r['mean']:.3f}  {r['sigma']:.3f}  {r['neff']:5.0f}"
              f"  {float(p['soft']):.3f}  {float(p['hard']):.3f}  {float(p['hs']):.3f}  {float(p['hm']):.3f}   {abs(r['mean'] - 0.718) + abs(r['sigma'] - 0.390):.3f}")
    print("worst three:", ", ".join(f"{t} {res[t]['D']:.3f}" for t in order[-3:]))
    for name, path, weighted in (("tune25 (production)", tune_file("tune25"), False), ("E906 generator", LEGACY, True)):
        r = compare(*read_pt(path, weighted), edges, cdf_data, data_reps)
        print(f"{name}: D = {r['D']:.4f} +- {r['err']['both']:.4f} (data {r['err']['data']:.4f}, sim {r['err']['sim']:.4f}), "
              f"mean {r['mean']:.3f}, sigma {r['sigma']:.3f}, Neff {r['neff']:.0f}")

def graph(x, y, ey=None):
    return ROOT.TGraphErrors(len(x), np.ascontiguousarray(x, dtype=float), np.ascontiguousarray(y, dtype=float),
                             np.zeros(len(x)), np.ascontiguousarray(np.zeros(len(x)) if ey is None else ey, dtype=float))

def plot(tunes, out):
    ROOT.gROOT.SetBatch(True)
    ROOT.gStyle.SetOptStat(0)
    edges, N, dN = load_data()
    cdf_data, data_reps = cumulative(N), data_replicas(N, dN)
    data_err = data_reps.std(axis=0)
    cols = [ROOT.kRed + 1, ROOT.kGreen + 2, ROOT.kAzure + 1, ROOT.kOrange + 1]

    c = ROOT.TCanvas("c", "", 800, 750)
    top = ROOT.TPad("top", "", 0, 0.32, 1, 1); top.SetBottomMargin(0.02); top.SetGrid(); top.Draw()
    bot = ROOT.TPad("bot", "", 0, 0, 1, 0.32); bot.SetTopMargin(0.03); bot.SetBottomMargin(0.34); bot.SetGrid(); bot.Draw()
    keep = []
    lo_x, hi_x = edges[0] - 0.05, edges[-1] + 0.05

    top.cd()
    frame = ROOT.TH1D("frame", "", 100, lo_x, hi_x)
    frame.SetMinimum(0); frame.SetMaximum(1.05)
    frame.GetXaxis().SetLabelSize(0)
    frame.GetYaxis().SetTitle("cumulative fraction"); frame.GetYaxis().SetTitleSize(0.055)
    frame.GetYaxis().SetLabelSize(0.05); frame.GetYaxis().SetTitleOffset(0.9)
    frame.Draw()
    leg = ROOT.TLegend(0.40, 0.14, 0.92, 0.36); leg.SetBorderSize(0); leg.SetFillStyle(0); leg.SetTextSize(0.038)
    results = []
    for t, col in zip(tunes, cols):
        pt, w = read_pt(tune_file(t))
        r = compare(pt, w, edges, cdf_data, data_replicas(N, dN))
        gs = graph(edges, r["cdf"]); gs.SetLineColor(col); gs.SetLineWidth(2); gs.Draw("L SAME")
        leg.AddEntry(gs, f"{t} (pythia8), N = {int((pt < edges[-1]).sum())}, D = {r['D']:.3f} #pm {r['err']['both']:.3f}", "l")
        reps = sim_replicas(pt[pt < edges[-1]], w[pt < edges[-1]], edges) - data_reps
        results.append((r["cdf"] - cdf_data, reps.std(axis=0), col)); keep.append(gs)
        print(f"{t}: D = {r['D']:.4f} +- {r['err']['both']:.4f} at pT edge {edges[np.argmax(np.abs(r['cdf'] - cdf_data))]:.2f}")
    gd = graph(edges, cdf_data, data_err); gd.SetMarkerStyle(21); gd.SetMarkerSize(1.0); gd.SetLineColor(ROOT.kBlack); gd.Draw("P SAME")
    leg.AddEntry(gd, "E906 LH2 data", "p"); leg.Draw()

    bot.cd()
    bf = ROOT.TH1D("bf", "", 100, lo_x, hi_x)
    lo = min((d - e).min() for d, e, _ in results); hi = max((d + e).max() for d, e, _ in results)
    bf.SetMinimum(min(-0.02, 1.2 * lo)); bf.SetMaximum(1.25 * hi)
    bf.GetXaxis().SetTitle("p_{T}^{#mu^{+}#mu^{-}} [GeV/c]"); bf.GetXaxis().SetTitleSize(0.13)
    bf.GetXaxis().SetLabelSize(0.11); bf.GetXaxis().SetTitleOffset(1.0)
    bf.GetYaxis().SetTitle("sim - data"); bf.GetYaxis().SetTitleSize(0.12); bf.GetYaxis().SetLabelSize(0.10)
    bf.GetYaxis().SetTitleOffset(0.45); bf.GetYaxis().SetNdivisions(505)
    bf.Draw()
    for x, e in zip(edges, data_err):
        b = ROOT.TBox(x - 0.03, -e, x + 0.03, e); b.SetFillColorAlpha(ROOT.kGray + 1, 0.45); b.SetLineWidth(0); b.Draw(); keep.append(b)
    zero = ROOT.TLine(lo_x, 0, hi_x, 0); zero.Draw(); keep.append(zero)
    for k, (diff, err, col) in enumerate(results):
        g = graph(edges + 0.02 * (k - (len(results) - 1) / 2), diff, err)
        g.SetMarkerStyle(20); g.SetMarkerSize(0.9); g.SetMarkerColor(col); g.SetLineColor(col); g.SetLineWidth(2)
        g.Draw("PL SAME"); keep.append(g)
    c.SaveAs(out)
    print("wrote", out)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rank", help="rank the 30 scan files by D")
    p = sub.add_parser("plot", help="cumulative distributions and sim - data")
    p.add_argument("--tunes", nargs="+", default=["tune01", "tune29", "tune25"])
    p.add_argument("--out", default="../../ana_note/figs/ks_cdf.png")
    args = ap.parse_args()
    rank() if args.cmd == "rank" else plot(args.tunes, args.out)
