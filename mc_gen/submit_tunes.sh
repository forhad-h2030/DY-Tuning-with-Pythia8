#!/bin/bash
# Submit one job set per DY tune config (phpythia8_DY_tune01.cfg ... tune10.cfg).
# Usage: ./submit_tunes.sh [do_sub=1] [njobs=100] [nevents=100]
# Job names are DY_tune01 ... DY_tune10.

dir_macros=$(dirname $(readlink -f $BASH_SOURCE))
do_sub=${1:-1}
njobs=${2:-100}
nevents=${3:-100}

cd $dir_macros
tunes=${4:-}  # optional: space-separated tune list, e.g. "tune02 tune03"
for cfg in phpythia8_DY_tune??.cfg; do
  tune=${cfg#phpythia8_DY_}
  tune=${tune%.cfg}
  if [ -n "$tunes" ] && [[ " $tunes " != *" $tune "* ]]; then continue; fi
  jobname=DY_$tune
  echo "=== $jobname: $cfg, $njobs jobs x $nevents events"
  ./gridsub.sh $jobname $do_sub $njobs $nevents $cfg || exit $?
done
