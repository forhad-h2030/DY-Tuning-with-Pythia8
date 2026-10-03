#!/bin/bash

dir_macros=$(dirname $(readlink -f $BASH_SOURCE))

jobname=$1
do_sub=$2
njobs=$3
nevents=$4
pythia_cfg=${5:-phpythia8_DY.cfg}

echo "njobs=$njobs"
echo "nevents=$nevents"
echo "pythia_cfg=$pythia_cfg"
if [ $do_sub == 1 ]; then
    echo "Grid mode."
    dir_data=/pnfs/e1039/scratch/users/$USER/DimuAnaRUS/mc_gen
    work=$dir_data/$jobname
    ln -nfs $dir_data data # for convenience
else
    echo "Local mode."
    work=$dir_macros/scratch/$jobname
fi

rm -rf         $work
mkdir -p       $work 
chmod -R 01755 $work

cd $dir_macros
tar -czvf $work/input.tar.gz *.C *.cfg *.opts ../setup.sh ../inst

for (( id=1; id<=$njobs; id++ )) ; do
  mkdir -p $work/$id/out
  chmod -R 01755 $work/$id
  cp -a $dir_macros/gridrun.sh $work/$id

  if [ $do_sub == 1 ]; then
    CMD="/exp/seaquest/app/software/script/jobsub_submit_spinquest.sh"
    CMD+=" --expected-lifetime='long'" # medium=8h, short=3h, long=23h
    CMD+=" -L $work/$id/log_gridrun.txt"
    CMD+=" -f $work/input.tar.gz"
    CMD+=" -d OUTPUT $work/$id/out"
    CMD+=" file://$work/$id/gridrun.sh $nevents $id $pythia_cfg"
    echo "$CMD"
    unbuffer $CMD |& tee $work/$id/log_jobsub_submit.txt
    RET_SUB=${PIPESTATUS[0]}
    if [ $RET_SUB -ne 0 ]; then exit $RET_SUB; fi
  else
    mkdir -p $work/$id/input
    cp -p $work/input.tar.gz $work/$id/input
    cd $work/$id
    $work/$id/gridrun.sh $nevents $id $pythia_cfg |& tee $work/$id/log_gridrun.txt
  fi
done
