"""Helpers shared by note_numbers.py and fig_sigma_kt.py: reconstructed dimuon pT and mass from the RUS files."""
import awkward as ak
import numpy as np

from final_files import FINAL_FILES, tune_file  # noqa: F401  (re-exported)

MUON_MASS = 0.1056  # GeV/c^2
BRANCHES = [f"rec_dimuon_{c}_{s}_tgt" for s in ("pos", "neg") for c in ("px", "py", "pz")]
TRIG = "evtPassTrigEmu"


def pair_pt_mass(tree, use_trigger=True, with_weight=False):
    """pT and mass of the first reconstructed mu+ mu- pair per event; the trigger flag is applied when the file has it."""
    want = BRANCHES + ([TRIG] if use_trigger and TRIG in tree.keys() else []) + (["weight"] if with_weight else [])
    a = tree.arrays(want, library="ak")
    has = (ak.num(a[BRANCHES[0]]) > 0) & (ak.num(a[BRANCHES[3]]) > 0)
    if TRIG in want:
        has = has & (a[TRIG] != 0)
    a = a[has]
    pxp, pyp, pzp, pxn, pyn, pzn = (ak.to_numpy(ak.firsts(a[b])) for b in BRANCHES)
    ep = np.sqrt(pxp**2 + pyp**2 + pzp**2 + MUON_MASS**2)
    en = np.sqrt(pxn**2 + pyn**2 + pzn**2 + MUON_MASS**2)
    px, py, pz = pxp + pxn, pyp + pyn, pzp + pzn
    mass = np.sqrt(np.maximum((ep + en) ** 2 - px**2 - py**2 - pz**2, 0))
    if with_weight:
        return np.hypot(px, py), mass, ak.to_numpy(a["weight"])
    return np.hypot(px, py), mass
