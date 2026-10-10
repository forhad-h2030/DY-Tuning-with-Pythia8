#!/bin/bash
# Submit a range of DY tune configs (default tune01 ... tune30) through submit_tunes.sh,
# after checking that the submission is safe.
#
# Usage: ./submit_scan.sh [-a first=1] [-b last=30] [-j njobs=100] [-n nevents=100]
#                         [-L] [-c] [-y] [-F]
#   -L  local mode (do_sub=0, runs the jobs here, for a small test: use -j 1 -n 5)
#   -c  check only: run all the checks and print the command, do not submit
#   -y  do not ask for confirmation
#   -F  allow overwriting existing job output (gridsub.sh runs rm -rf on each job directory!)
#
# Examples: ./submit_scan.sh -c                      # check everything
#           ./submit_scan.sh -a 1 -b 1 -L -j 1 -n 5   # local test of tune01
#           ./submit_scan.sh                          # submit tune01-30, 100 jobs x 100 events

dir=$(dirname "$(readlink -f "$BASH_SOURCE" 2>/dev/null || echo "$0")")
first=1; last=30; njobs=100; nevents=100; do_sub=1; check_only=0; assume_yes=0; force=0
while getopts "a:b:j:n:LcyF" opt; do
  case $opt in
    a) first=$OPTARG ;;
    b) last=$OPTARG ;;
    j) njobs=$OPTARG ;;
    n) nevents=$OPTARG ;;
    L) do_sub=0 ;;
    c) check_only=1 ;;
    y) assume_yes=1 ;;
    F) force=1 ;;
    *) sed -n '2,15p' "$0"; exit 1 ;;
  esac
done

cd "$dir" || exit 1
tunes=""
for (( i=first; i<=last; i++ )); do tunes+=$(printf 'tune%02d ' "$i"); done
tunes=${tunes% }

fail=0
err() { echo "ERROR: $*"; fail=1; }

# 1. every cfg exists
missing=""
for t in $tunes; do [ -e "phpythia8_DY_$t.cfg" ] || missing+=" $t"; done
[ -n "$missing" ] && err "missing cfg files for:$missing (copy them to $dir)"

# 2. Fun4Sim.C must use the cfg passed by gridrun.sh, not a hardcoded one
if ! grep -qE '^[[:space:]]*pythia8->set_config_file\(pythia_cfg\);' Fun4Sim.C; then
  err "Fun4Sim.C does not use set_config_file(pythia_cfg): every job would run the default config"
fi

# 3. all selected tunes share the same mass range
ranges=$(for t in $tunes; do
  [ -e "phpythia8_DY_$t.cfg" ] && grep -hE '^PhaseSpace:mHat(Min|Max)' "phpythia8_DY_$t.cfg" | awk '{print $1 $2 $3}' | tr '\n' ' '; echo
done | sort -u | grep -v '^$')
if [ "$(echo "$ranges" | wc -l)" -gt 1 ]; then
  err "the selected tunes have different mHat ranges:"; echo "$ranges"
else
  echo "mass range of all selected tunes: $ranges"
fi

# 4. do not wipe existing job output on /pnfs
if [ $do_sub == 1 ]; then
  base=/pnfs/e1039/scratch/users/$USER/DimuAnaRUS/mc_gen
  for t in $tunes; do
    if [ -n "$(ls -A "$base/DY_$t" 2>/dev/null)" ]; then
      if [ $force == 1 ]; then echo "WARNING: $base/DY_$t exists and will be wiped (-F)"
      else err "$base/DY_$t already has content; gridsub.sh would wipe it (use -F to allow)"; fi
    fi
  done
fi

n=$(echo $tunes | wc -w)
echo "tunes: $tunes"
echo "$n tunes x $njobs jobs x $nevents events, $([ $do_sub == 1 ] && echo grid || echo local) mode"
cmd="./submit_tunes.sh $do_sub $njobs $nevents \"$tunes\""
echo "command: $cmd"

if [ $fail != 0 ]; then echo "Checks failed, nothing submitted."; exit 1; fi
if [ $check_only == 1 ]; then echo "Checks passed (check only, nothing submitted)."; exit 0; fi

if [ $assume_yes != 1 ]; then
  read -r -p "Submit? [y/N] " ans
  [ "$ans" == "y" ] || [ "$ans" == "Y" ] || { echo "Aborted."; exit 1; }
fi

[ -e ../setup.sh ] && source ../setup.sh
log=submit_scan_$(date +%Y%m%d_%H%M%S).log
echo "logging to $log"
./submit_tunes.sh $do_sub $njobs $nevents "$tunes" 2>&1 | tee "$log"
exit ${PIPESTATUS[0]}
