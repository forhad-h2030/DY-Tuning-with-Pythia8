# Event Generation and Reconstruction with RUS

This module allows you to perform event generation and reconstruction using the **`Fun4AllSim.C`** macro. Similar to the [SimChainDev module](https://github.com/E1039-Collaboration/e1039-analysis/tree/master/SimChainDev), this script facilitates event simulation, but with an **additional feature**: support for the **RUS file manager** for input and output handling.


## Steps to Run MC Simulations:
1. Clone the repository:
   git clone https://github.com/uva-spin/DimuAnaRUS 

2. **Compile the script** (if you haven’t done so already):
    ```bash
    cd DimuAnaRUS/mc_gen 
    source ../setup.sh    
    cmake-this
    make-this
    ```
3. **Run a test job locally** and check the output files:
    ```bash
    root -b 'Fun4AllSim.C(5)'
    ```
4. **If everything looks correct**, run the job on the Rivanna HPC with a few events:
    ```bash
    ./jobscript.sh test 1 10
    ```
5. **For large-scale submissions**, compute the event processing as explained in the following link:  
   [SpinQuest Monte Carlo Generation on Rivanna](https://confluence.admin.virginia.edu/display/twist/SpinQuest+Monte+Carlo+Generation+on+Rivanna),  
   and submit a job using the following example:
    ```bash
    ./jobscript.sh DYTarget 100 100
    ```
6. **Check your output files** at:
    ```bash
    /sfs/weka/scratch/<user_name>/MC

# Submitting the DY Tune Scan

`phpythia8_DY_tune01.cfg` to `phpythia8_DY_tune10.cfg` are copies of `phpythia8_DY.cfg` (virtual photon, `mHatMin = 1.0`, `mHatMax = 8.0`, `pTHatMinDiverge = 0.5`). They differ only in `BeamRemnants:primordialKThard` and `SpaceShower:pT0Ref`. Tune 01 uses the Pythia defaults (1.8, 2.0) and is the baseline.

`submit_tunes.sh` submits one job set per tune, named `DY_tune01` to `DY_tune10`:

```bash
./submit_tunes.sh [do_sub=1] [njobs=100] [nevents=100]
```

```bash
./submit_tunes.sh 0 2 10   # local test: 2 jobs x 10 events per tune
./submit_tunes.sh          # grid: 100 jobs x 100 events per tune
```

To run a single tune, or any other config, pass it to `gridsub.sh` as the fifth argument:

```bash
./gridsub.sh DY_tune03 1 100 100 phpythia8_DY_tune03.cfg
```

The config can also be chosen when running the macro directly:

```bash
root -b -q 'Fun4Sim.C(10, "phpythia8_DY_tune03.cfg")'
```

Outputs go to `<output_dir>/<jobname>/<job_id>/out`, so each tune is kept separate.

# RUS File Options in `Fun4AllSim.C`

To configure the RUS file options in `Fun4AllSim.C`, use the following settings:

```cpp
DimuAnaRUS* dimuAna = new DimuAnaRUS();
dimuAna->SetTreeName("tree");          // Set tree name
dimuAna->SetMCTrueMode(true);          // Set to false if true particle info is not needed
dimuAna->SetSaveOnlyDimuon(true);      // Set to false if not saving dimuons
dimuAna->SetRecoMode(true);            // Set to false if reconstruction is not needed
dimuAna->SetOutputFileName("RUS.root");
se->registerSubsystem(dimuAna);

