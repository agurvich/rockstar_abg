import os
import glob
import shutil

import numpy as np

from .utilities import io as ut_io
from .gizmo_analysis import gizmo_io

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
    
    run_rockstar(workpath,snapshot_indices=snapshot_indices,run=run)

def run_rockstar(workpath,snapshot_indices=None,run=False):

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

    ## steps 6 & 7 & 8 generate auto-rockstar.cfg and mimic submitting from directory
    ##  runs rockstar and generates output files to /path/to/rockstar_dm/catalog
    current_dir = os.path.dirname(__file__)
    halo_directory = os.path.join(
        current_dir,
        'executables',
        'rockstar-galaxies')
    #submit_rockstar(halo_directory,run=run)

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

def submit_rockstar(halo_directory=None,run=False):

    # names of files and directories
    if halo_directory is None:
        halo_directory = os.environ['HOME'] + '/local/halo/rockstar-galaxies/'

    executable_file_name = os.path.join(halo_directory,'rockstar-galaxies')
    catalog_directory = 'catalog/'
    config_file_name_restart = 'restart.cfg'

    os.system('umask 0022')  # set permission of files created to be read-only for group and other

    # set and print compute parameters
    SubmissionScript = ut_io.SubmissionScriptClass('slurm')

    # check if restart config file exists - if so, initiate restart job
    config_file_name_restart = glob.glob(catalog_directory + config_file_name_restart)

    if len(config_file_name_restart) > 0:
        config_file_name = config_file_name_restart[0]
    else:
        # set number of file blocks per snapshot, or read from snapshot header
        snapshot_block_number = None
        if not snapshot_block_number:
            simulation_directory = '../../.'  # relative path of base simulation directory
            try:
                header = gizmo_io.Read.read_header(
                    simulation_directory, snapshot_value_kind='index', snapshot_value=500
                )
            except OSError:
                header = gizmo_io.Read.read_header(
                    simulation_directory, snapshot_value_kind='index', snapshot_value=20
                )
            except OSError:
                header = gizmo_io.Read.read_header(
                    simulation_directory, snapshot_value_kind='index', snapshot_value=0
                )
            except OSError:
                print(f'! cannot read snapshot file in {simulation_directory} to get file block count')
            snapshot_block_number = header['file.number.per.snapshot']

        if snapshot_block_number == 1:
            config_file_name = 'rockstar_config.txt'
        else:
            config_file_name = f'rockstar_config_blocks{snapshot_block_number}.txt'

        config_file_name = os.path.join(halo_directory,config_file_name)

    if not run:
        print("Running from",os.getcwd())
    fn = os.system if run else print

    # start server
    fn(f'{executable_file_name} -c {config_file_name} &')

    # start worker
    fn(
        f'sleep 1 ; {executable_file_name} -c {catalog_directory}auto-rockstar.cfg'
        + ' >> rockstar_jobs/rockstar_log.txt'
    )

    SubmissionScript.print_runtime()

def modify_rockstar_config(workpath):

    starting_snap = 60 ## TODO replace
    max_snap = 60

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