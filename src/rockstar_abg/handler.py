import os
import glob
import h5py

import numpy as np


from .submit import submit_hdf5, submit_particle, submit_rockstar,submit_consistent_trees,modify_rockstar_config


def main(
    savename,
    sim_path = None,
    suite_name='fire3_compatability/core',
    snapshot_indices=None,
    run=False):

    if sim_path is None:
        sim_path = '/scratch/projects/xsede/GalaxiesOnFIRE'

        workpath = os.path.join(
            sim_path,
            suite_name,
            savename)
    else:
        if os.path.basename(sim_path) != savename:
            workpath = os.path.join(sim_path,savename)
    print(f"interpreted workpath as: {sim_path}")
    
    ## creates directories and moves to halo/rockstar_dm
    workpath,fire2,snapshot_indices = initialize_workpath(workpath,snapshot_indices)

    ## generates rockstar halos
    run_rockstar(snapshot_indices,run=run,fire2=fire2)

    ## generates merger tree files
    run_consistent_trees(workpath,snapshot_indices,run=run)

    ## convert to hdf5 format for easier read-in
    submit_hdf5(workpath,snapshot_indices,run=run)

    ## make particle files
    submit_particle(
        'star',
        snapshot_indices,
        run=run)

    ## takes forever and doesn't seem to be standard
    """
    submit_particle(
        'gas',
        snapshot_index_min=snapshot_indices.min(),
        snapshot_index_max=snapshot_indices.max(),
        run=run)
    """

def initialize_workpath(workpath,snapshot_indices):
    ## steps 1 & 2 
    ##  if you're here you already did this-- setup.py will compile executables

    ## step 3 make halo directories if necessary
    try: make_halo_dirs(workpath)
    except PermissionError as e:
        print(f"PermissionError - Can't write to {e.filename}")
        raise e

    ## step 4 choose a rockstar config file-- happens in step 6

    ## step 5 generate snapshot indices
    snappath = os.path.join(workpath,'output')
    potential_snapshots = [
        fname for fname in os.listdir(snappath) 
        if ('snapdir' in fname) or ('snapshot' in fname and 'hdf5' in fname)]

    if snapshot_indices is None: 
        snapshot_indices = sorted([int(val.split('_')[-1].replace('.hdf5','')) for val in potential_snapshots])

    consecutive_indices = np.arange(np.min(snapshot_indices),np.max(snapshot_indices)+1,dtype=int) 
    missing = set(consecutive_indices) - set(snapshot_indices)
    if len(missing) > 0: raise IOError("Consistent trees requires consecutive snapshots w.o. gaps.")

    ## determine if we're running on fire3 or fire2
    ##  by looking at the header info (particularly, whether the underscore is present in Omega_Lambda)
    fname = os.path.join(snappath,sorted(potential_snapshots)[0])
    ## handle the absurd scenario where we have nested snapdirs or something idk
    while os.path.isdir(fname):
        potential_snapshots = [
            fname.split('_')[-1] for fname in os.listdir(fname) 
            if ('snapdir' in fname) or ('snapshot' in fname and 'hdf5' in fname)]
        if len(fname) == 0: raise IOError(f"Couldn't find a snapshot in {fname}")
        fname = os.path.join(snappath,sorted(potential_snapshots)[0])

    with h5py.File(fname,'r') as handle: fire2 = 'OmegaLambda' in handle['Header'].attrs.keys()

    ##  move to directory where we want the output to be
    workpath = os.path.join(workpath,'halo','rockstar_dm')
    os.chdir(workpath)
    ##  save snapshot_indices.txt file
    np.savetxt('snapshot_indices.txt',np.array(snapshot_indices).T,fmt='%03d')
    return workpath,fire2,snapshot_indices

def run_rockstar(snapshot_indices,run=False,fire2=False):
    ## steps 6 & 7 & 8 generate auto-rockstar.cfg and mimic submitting from directory
    ##  runs rockstar and generates output files to /path/to/rockstar_dm/catalog
    halo_directory = os.path.dirname(__file__)
    rockstar_directory = os.path.join(
        halo_directory,
        'executables',
        'rockstar-galaxies'+'-fire2'*fire2)
    submit_rockstar(snapshot_indices,rockstar_directory,run=run)

def run_consistent_trees(workpath,snapshot_indices,run=False):
    ## step 9 :
    """--- set up Consistent-Trees to generate merger trees --- 
    Consistent-Trees runs best if you first modify catalog/rockstar.cfg (around line 50) as follows:
        set STARTING_SNAP = NNN, where out_NNN.txt is the first snapshot with any halos in it
        change to NUM_SNAPS = 500 (or = 600 for FIRE-2)
        comment out (with a #) the line named SNAPSHOT_NAMES, so it looks like: 
            #SNAPSHOT_NAMES = "snapshot_indices.txt"
    Generate the merger tree configuration file (catalog/outputs/merger_tree.cfg) from the rockstar configuration file (catalog/rockstar.cfg) as follows:
        perl ~/local/halo/rockstar-galaxies/scripts/gen_merger_cfg.pl catalog/rockstar.cfg
    Check (and modify if necessary) catalog/outputs/merger_tree.cfg (around line 12) to ensure the following (so the tree runs on the entire simulation):
        BOX_DIVISIONS=1
    """
    ##  make the suggested modifications
    ## -1 because num_snaps means something different for consistent trees than rockstar, what a cluster-f***
    modify_rockstar_config(workpath,snapshot_indices[0],snapshot_indices[-1]-1)
    halo_directory = os.path.dirname(__file__)
    rockstar_directory = os.path.join(
        halo_directory,
        'executables',
        'rockstar-galaxies')
    ##  generate merger tree config file and ensure BOX_DIVISIONS=1
    generate_merger_tree_config(workpath,rockstar_directory)

    ## step 10: run consistent-trees
    submit_consistent_trees(workpath,halo_directory,run=run)

def make_halo_dirs(workpath):
    prefix = 'halo/rockstar_dm/'
    suffixes = [
        'rockstar_jobs',
        'catalog',
        'catalog_hdf5']

    for suffix in suffixes:
        dirpath = os.path.join(workpath,prefix,suffix)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)

def generate_merger_tree_config(workpath,rockstar_directory):
    #perl ~/local/halo/rockstar-galaxies/ catalog/rockstar.cfg
    os.system('perl %s/scripts/gen_merger_cfg.pl %s/catalog/rockstar.cfg'%(rockstar_directory,workpath))

    ## modify to ensure BOX_DIVISIONS=1, per Andrew's instructions.
    ##  not sure what circumstances would make it not 1 but now we can
    ##  be sure. 
    cfg_file = os.path.join(workpath,'catalog','outputs','merger_tree.cfg')
    with open(cfg_file,'r') as handle:
        lines = handle.readlines()
        for i,line in enumerate(lines):
            if 'BOX_DIVISIONS' in line:
                lines[i] = 'BOX_DIVISIONS=1\n'
                
    ## overwrite with the modification
    with open(cfg_file,'w') as handle:
        handle.write(''.join(lines))
