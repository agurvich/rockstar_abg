import os
import glob

import numpy as np


from .submit import submit_hdf5, submit_particle, submit_rockstar,submit_consistent_trees

FIREPATH = '/scratch/projects/xsede/GalaxiesOnFIRE'

def main(
    savename,
    suite_name='fire3_compatability/core',
    snapshot_indices=None,
    run=False):

    workpath = os.path.join(
        FIREPATH,
        suite_name,
        savename)
    
    ## creates directories and moves to halo/rockstar_dm
    workpath = initialize_workpath(workpath,snapshot_indices)

    ## generates rockstar halos
    run_rockstar(run=run)

    ## generates merger tree files
    run_consistent_trees(workpath,run=run)

    ## convert to hdf5 format for easier read-in
    submit_hdf5(workpath,run=run)

    ## make particle files
    submit_particle(
        'star',
        snapshot_index_min=snapshot_indices.min(),
        snapshot_index_max=snapshot_indices.max(),
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
    make_halo_dirs(workpath)

    ## step 4 choose a rockstar config file-- happens in step 6

    ## step 5 generate snapshot indices
    if snapshot_indices is None: snapshot_indices = np.arange(1,501)

    ##  move to directory where we want the output to be
    workpath = os.path.join(workpath,'halo','rockstar_dm')
    os.chdir(workpath)
    ##  save snapshot_indices.txt file
    np.savetxt('snapshot_indices.txt',np.array(snapshot_indices).T,fmt='%03d')
    return workpath

def run_rockstar(run=False):
    ## steps 6 & 7 & 8 generate auto-rockstar.cfg and mimic submitting from directory
    ##  runs rockstar and generates output files to /path/to/rockstar_dm/catalog
    halo_directory = os.path.dirname(__file__)
    rockstar_directory = os.path.join(
        halo_directory,
        'executables',
        'rockstar-galaxies')
    submit_rockstar(rockstar_directory,run=run)

def run_consistent_trees(workpath,run=False):
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
    modify_rockstar_config(workpath)
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

def modify_rockstar_config(workpath):

    starting_snap,max_snap = find_first_snapshot_with_halos(workpath)

    cfg_file = os.path.join(workpath,'catalog','rockstar.cfg')
    with open(cfg_file,'r') as handle:
        lines = handle.readlines()
        for i in range(len(lines)):
            line = lines[i]
            if 'STARTING_SNAP' in line:
                print(line)
                lines[i] = 'STARTING_SNAP = %03d\n'%starting_snap
            elif 'NUM_SNAPS' in line:
                print(line)
                lines[i] = 'NUM_SNAPS = %03d\n'%max_snap
            elif 'SNAPSHOT_NAMES' in line:
                ## only do it once, in case config has already been modified
                if line[0] != '#':
                    print(line)
                    lines[i] = '#SNAPSHOT_NAMES = "snapshot_indices.txt"\n'

    with open(cfg_file,'w') as handle:
        handle.write(''.join(lines))

def find_first_snapshot_with_halos(workpath):
    files = glob.glob(
        os.path.join(workpath,'catalog','halos_*.0.ascii'))
    files = sorted(files)
    break_flag = False
    if len(files) == 0:
        raise IOError("Couldn't find halo files in",os.path.join(workpath,'catalog'))
    for file in files:
        with open(file,'r') as handle:
            for line in handle:
                if line[0] !='#':
                    break_flag = True
                    break
        if break_flag: break
    starting_snap = int(os.path.basename(file).split('_')[1].split('.')[0])
    max_snap = int(os.path.basename(files[-1]).split('_')[1].split('.')[0])
    return starting_snap,max_snap

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