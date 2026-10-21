# Scripts behind the note

Run from this directory. ROOT scripts need `PYTHONPATH=$(root-config --libdir)`.

| Script | Output |
|---|---|
| `ks_tune.py rank` (ROOT) | KS distance D, mean and sigma of pT (ranking and main tables) |
| `ks_tune.py plot` (ROOT) | `ks_cdf.png` |
| `overlay_pt_root.py` (ROOT) | `overlay_pt_main.png` |
| `fig_grid_root.py` (ROOT) | `overlay_grid_root.png` |
| `note_numbers.py` | chi2, mass fractions, mean pT against mass (full simulation) |
| `pythia_sensitivity.py` | sensitivity table (standalone PYTHIA 8.310) |
| `fig_sigma_kt.py` | kT width against mass (not in the note) |

`final_files.py` and `pt_vs_config.py` are helpers.
