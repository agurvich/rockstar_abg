#!/bin/bash

## usually one of bash, less, sbatch, what to execute on the dummy script
this_command=$1 

## job preamble with allocation, etc...
preamble=${HOME}/ss/preamble.sh

## target directory whose simulations we should loop over and generate halo files for
sim_path=/projects/b1026/snapshots/restartdisktest/m11a_m2e3

for sim_dir in ${sim_path}/*
do
    name=`basename ${sim_dir}`
    ## arg0: directory to simulations
    ## arg1: name of simulation
    if [ -d  ${sim_dir}/output ]
    then

        if [ -f ${sim_dir}/halo/rockstar_dm/catalog_hdf5/halo_060.hdf5 ] 
        then
            echo ${name} "is already done!"
        else
            ## sets job_name to the last string delimited by _ (lol)
            IFS='_' read -ra ADDR <<< ${name}
            for job_name in "${ADDR[@]}"; do
                sleep 0
            done

            cat ${preamble} > temp.sh 
            # don't need this because it's already in my preamble on Quest
            #echo "#SBATCH -t 48:00:00        # run time (hh:mm:ss) - 48 hours" >> temp.sh
            echo "#SBATCH -J ${job_name}_rockstar         # job name" >> temp.sh
            echo "python runner.py ${sim_path} ${name}" >> temp.sh
            ${this_command} temp.sh
            rm temp.sh
        fi
    else
        echo ${name} "doesn't have an output directory"
        sleep 1
    fi

done
