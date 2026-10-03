## Goal
Tune the PYTHIA8 Drell-Yan (virtual photon) settings for SpinQuest so the generated kinematics, in particular the dimuon pT distribution and invariant mass (IM), are not distorted. The configs use `mHatMin = 1.0`, `mHatMax = 8.0` and `pTHatMinDiverge = 0.5`, and scan `BeamRemnants:primordialKThard` and `SpaceShower:pT0Ref`.

## Summary
- `mc_gen/`: event generation and reconstruction (`Fun4Sim.C`), the base config `phpythia8_DY.cfg`, ten tune configs `phpythia8_DY_tune01.cfg` to `tune10.cfg`, and `submit_tunes.sh` to submit them (100 jobs x 100 events each). See `mc_gen/README.md`.
- `src/`: the `DimuAnaRUS` module, which writes the MC and reconstructed output in RUS (ROOT Universal Structure) format.

## Build
```
source setup.sh
cmake-this
make-this
```
