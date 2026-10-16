## Goal
Tune the PYTHIA8 Drell-Yan settings for SpinQuest so the generated kinematics, in particular the dimuon pT distribution and invariant mass (IM), are not distorted. The configs use `mHatMin = 0.25`, `mHatMax = 10.0` and `pTHatMinDiverge = 0.5`, and scan four primordial-kT parameters (`BeamRemnants:primordialKTsoft`, `primordialKThard`, `halfScaleForKT`, `halfMassForKT`).

## Summary
- `mc_gen/`: event generation and reconstruction (`Fun4Sim.C`), the base config `phpythia8_DY.cfg`, the tune configs `phpythia8_DY_tune01.cfg` to `tune30.cfg`.
- `src/`: the `DimuAnaRUS` module, which writes the MC and reconstructed output in RUS (ROOT Universal Structure) format.

## Build
```
source setup.sh
cmake-this
make-this
```
