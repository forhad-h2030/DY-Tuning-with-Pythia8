#!/usr/bin/env python3
"""One-at-a-time sensitivity of the generator-level dimuon pT to PYTHIA 8 settings (note sensitivity table, sensitivity_8.310.csv).
Standalone PYTHIA, fixed-target pp at 120 GeV, process 223 (gamma* 2->2, mu+ mu- kept), hadronization off. Mean and sigma of the pair pT
are printed for all dimuons and for both muons in 10 < pz < 120 (acc). Do not use --process 21: it is not equivalent (softer pair pT).
Run: PYTHONPATH=<dir with pythia8> python3 pythia_sensitivity.py [-n 200000] [-j 4] [--csv out.csv]
"""
import argparse
import csv
import math
import multiprocessing as mp
import os
import time

PZ_MIN, PZ_MAX = 10.0, 120.0

BASE = [
    "Beams:frameType = 2", "Beams:idA = 2212", "Beams:idB = 2212", "Beams:eA = 120.", "Beams:eB = 0.",
    "PhaseSpace:mHatMin = 0.25", "PhaseSpace:mHatMax = 10.0",
    "HadronLevel:all = off", "Next:numberCount = 0",
]
PROC_21 = ["WeakSingleBoson:ffbar2gmZ = on", "WeakZ0:gmZmode = 1", "23:mMin = 0.25", "23:mMax = 10.0",
           "23:onMode = off", "23:onIfMatch = 13 -13"]
PROC_22 = ["WeakSingleBoson:ffbar2ffbar(s:gm) = on", "PhaseSpace:pTHatMinDiverge = 0.5"]

# (setting, default shown for information, values to try)
VARIATIONS = [
    ("BeamRemnants:primordialKThard", 1.8, [0.5, 2.5]),
    ("BeamRemnants:primordialKTsoft", 0.9, [0.3, 1.5]),
    ("BeamRemnants:halfScaleForKT", 1.5, [0.5, 4.0]),
    ("BeamRemnants:halfMassForKT", 1.0, [0.25, 3.0]),
    ("BeamRemnants:reducedKTatHighY", 0.5, [0.0, 1.0]),
    ("BeamRemnants:primordialKTremnant", 0.4, [0.1, 1.0]),
    ("BeamRemnants:primordialKT", "on", ["off"]),
    ("SpaceShower:pT0Ref", 2.0, [0.5, 4.0]),
    ("SpaceShower:alphaSvalue", 0.1365, [0.10, 0.18]),
    ("SpaceShower:pTmin", 0.2, [0.1, 1.0]),
    ("SpaceShower:pTmaxMatch", 0, [1, 2]),
    ("SpaceShower:pTdampMatch", 3, [0, 1]),
    ("SpaceShower:alphaSorder", 1, [0, 2]),
    ("SpaceShower:rapidityOrder", "on", ["off"]),
    ("PartonLevel:ISR", "on", ["off"]),
    ("PartonLevel:MPI", "on", ["off"]),
    ("PartonLevel:FSR", "on", ["off"]),
    ("MultipartonInteractions:pT0Ref", 2.28, [1.5, 3.5]),
    ("PDF:pSet", 13, [2, 8]),
]


def run(args):
    """Generate n events with the given settings. Returns (n_all, sum_pt, sum_pt2, n_acc, sum_pt_a, sum_pt2_a)."""
    label, settings, n, seed, proc = args
    try:
        import pythia8
    except ImportError:
        import pythia8mc as pythia8

    xml = os.path.join(os.path.dirname(pythia8.__file__), "share", "Pythia8", "xmldoc")
    if "PYTHIA8DATA" not in os.environ and os.path.isdir(xml):  # wheels: the xml files sit next to the module
        os.environ["PYTHIA8DATA"] = xml
    p = pythia8.Pythia("", False)
    for s in BASE + (PROC_21 if proc == 21 else PROC_22) + settings + ["Random:setSeed = on", f"Random:seed = {seed}"]:
        p.readString(s)
    if not p.init():
        return label, None
    na = sa = sa2 = nc = sc = sc2 = 0.0
    ev = p.event
    for _ in range(n):
        if not p.next():
            continue
        mus = []
        for i in range(ev.size()):
            pt = ev[i]
            if pt.isFinal() and abs(pt.id()) == 13:
                mus.append(pt)
        if len(mus) != 2 or mus[0].id() * mus[1].id() > 0:
            continue
        px = mus[0].px() + mus[1].px()
        py = mus[0].py() + mus[1].py()
        v = math.hypot(px, py)
        na += 1; sa += v; sa2 += v * v
        if all(PZ_MIN < m.pz() < PZ_MAX for m in mus):
            nc += 1; sc += v; sc2 += v * v
    return label, (na, sa, sa2, nc, sc, sc2)


def stats(n, s, s2):
    if n < 2:
        return float("nan"), float("nan"), float("nan"), float("nan")
    m = s / n
    sig = math.sqrt(max(s2 / n - m * m, 0) * n / (n - 1))
    return m, sig / math.sqrt(n), sig, sig / math.sqrt(2 * (n - 1))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("-n", type=int, default=200000, help="generated events per setting (about 1/8 end up as mu+ mu-)")
    ap.add_argument("--process", type=int, choices=[21, 22], default=22)
    ap.add_argument("--set", action="append", default=[], metavar="SETTING", help="extra setting for every run, e.g. --set 'PhaseSpace:mHatMin = 1.0'")
    ap.add_argument("-j", type=int, default=max(1, (os.cpu_count() or 2) - 1), help="parallel jobs")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--only", nargs="*", default=None, help="restrict to these setting names")
    ap.add_argument("--check-process", action="store_true", help="compare the 2->1 and 2->2 process at baseline")
    args = ap.parse_args()

    jobs = []
    if args.check_process:
        jobs = [("baseline 2->1", [], args.n, args.seed, 21), ("baseline 2->2", [], args.n, args.seed, 22)]
    else:
        jobs.append(("baseline", list(args.set), args.n, args.seed, args.process))
        for name, dflt, vals in VARIATIONS:
            if args.only and name not in args.only:
                continue
            for v in vals:
                jobs.append((f"{name} = {v}", list(args.set) + [f"{name} = {v}"], args.n, args.seed, args.process))

    t0 = time.time()
    with mp.get_context("spawn").Pool(args.j) as pool:
        res = dict(pool.map(run, jobs, chunksize=1))
    print(f"{len(jobs)} runs of {args.n} events in {time.time() - t0:.0f} s\n")

    base = res.get(jobs[0][0])
    b_all = stats(*[base[i] for i in (0, 1, 2)])
    b_acc = stats(*[base[i] for i in (3, 4, 5)])
    rows = []
    hdr = f"{'setting':<42}{'N(mumu)':>8}{'N(acc)':>8}{'acc %':>7}{'mean(all)':>11}{'sigma(all)':>11}{'mean(acc)':>11}{'sigma(acc)':>11}{'d mean(acc)':>13}{'d sigma(acc)':>14}{'signif':>8}"
    print(hdr)
    for label, *_ in jobs:
        r = res[label]
        if r is None:
            print(f"{label:<42}  init failed (setting not known or out of range in this Pythia version)")
            continue
        ma, dma, sa, dsa = stats(r[0], r[1], r[2])
        mc, dmc, sc, dsc = stats(r[3], r[4], r[5])
        dm, ds = mc - b_acc[0], sc - b_acc[2]
        sig = abs(dm) / math.hypot(dmc, b_acc[1]) if label != jobs[0][0] else 0.0
        rows.append([label, 100 * r[3] / max(r[0], 1), ma, sa, mc, sc, dm, ds, sig, dmc, dsc])
        print(f"{label:<42}{int(r[0]):8d}{int(r[3]):8d}{100 * r[3] / max(r[0], 1):7.1f}{ma:11.4f}{sa:11.4f}{mc:11.4f}{sc:11.4f}{dm:+13.4f}{ds:+14.4f}{sig:8.1f}")
    print(f"\nbaseline statistical error on the mean (acc): {b_acc[1]:.4f}, on sigma: {b_acc[3]:.4f}")
    if args.csv:
        with open(args.csv, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["setting", "acc_pct", "mean_all", "sigma_all", "mean_acc", "sigma_acc", "dmean_acc",
                        "dsigma_acc", "signif", "err_mean_acc", "err_sigma_acc"])
            w.writerows(rows)


if __name__ == "__main__":
    main()
