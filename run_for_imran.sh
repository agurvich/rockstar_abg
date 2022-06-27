#!/bin/bash

sim_path=/projects/b1026/isultan/halos

for sim_dir in ${sim_path}/*
do
    name=`basename ${sim_dir}`
    ## arg0: directory to simulations
    ## arg1: name of simulation
    python runner.py ${sim_path} ${name}
done
