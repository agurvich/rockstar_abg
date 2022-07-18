import os
import glob
import subprocess
import time

import numpy as np

from .utilities import io as ut_io
from .gizmo_analysis import gizmo_io
from .halo_analysis import halo_io

def modify_rockstar_config(
    workpath,
    source=None,
    target=None,
    starting_snap=None,
    max_snap=None):

    if starting_snap is None or max_snap is None:
        starting_snap,max_snap = find_first_snapshot_with_halos(workpath)

    if source is None: source = os.path.join(workpath,'catalog','rockstar.cfg')
    if target is None: target = source
    with open(source,'r') as handle:
        lines = handle.readlines()
        for i in range(len(lines)):
            line = lines[i]
            if 'STARTING_SNAP = ' in line:
                lines[i] = 'STARTING_SNAP = %03d\n'%starting_snap
                print(line,'->',lines[i])
            elif 'NUM_SNAPS = ' in line:
                lines[i] = 'NUM_SNAPS = %03d\n'%(max_snap)
                print(line,'->',lines[i])
            elif 'SNAPSHOT_NAMES' in line:
                ## only do it once, in case config has already been modified
                if line[0] != '#':
                    lines[i] = '#SNAPSHOT_NAMES = "snapshot_indices.txt"\n'
                    print(line.replace('\n',''),'->',lines[i])

    with open(target,'w') as handle:
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

def submit_rockstar(snapshot_indices,rockstar_directory=None,run=False):
    #time.sleep(2)

    # names of files and directories
    if rockstar_directory is None:
        rockstar_directory = os.environ['HOME'] + '/local/halo/rockstar-galaxies/'

    executable_file_name = os.path.join(rockstar_directory,'rockstar-galaxies')
    catalog_directory = 'catalog/'
    config_file_name_restart = 'restart.cfg'

    os.system('umask 0022')  # set permission of files created to be read-only for group and other

    # set and print compute parameters
    SubmissionScript = ut_io.SubmissionScriptClass('slurm')

    # check if restart config file exists - if so, initiate restart job
    config_file_name_restart = glob.glob(catalog_directory + config_file_name_restart)

    if len(config_file_name_restart) > 0:
        config_file_name = config_file_name_restart[0]
        restart_snap = None
        with open(os.path.join(os.getcwd(),config_file_name),'r') as handle:
            for line in handle.readlines():
                if 'RESTART_SNAP =' in line: restart_snap = eval(line.split('=')[1])
    else:
        restart_snap = None

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

        config_file_name = os.path.join(rockstar_directory,config_file_name)
        new_config_file_name = os.path.join(os.getcwd(),'rockstar_jobs',os.path.basename(config_file_name))
        modify_rockstar_config(None,config_file_name,new_config_file_name,snapshot_indices[0],snapshot_indices[-1])
        config_file_name = new_config_file_name

    if restart_snap is not None and restart_snap == (len(snapshot_indices)-1):
        check_exists_catalog = os.path.join(
            os.getcwd(),
            'catalog',
            f'halos_{restart_snap:03d}*')
        
        check_exists_outlist = os.path.join(
            os.getcwd(),
            'catalog',
            f'out_{restart_snap:03d}.list')

        files = glob.glob(check_exists_catalog)
        if len(files) > 0 and os.path.isfile(check_exists_outlist): 
            print("<<<< Already produced rockstar catalogs, skipping <submit_rockstar> >>>>")
            run = False

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

    if fn is not print: SubmissionScript.print_runtime()
    #time.sleep(2)

def submit_consistent_trees(workpath,halo_directory,run=False):
    #time.sleep(2)

    # directories and files
    if halo_directory is None:
        halo_directory = os.environ['HOME'] + '/local/halo/'

    rockstar_directory = os.path.join(halo_directory,'executables','rockstar-galaxies')
    consistentrees_directory = os.path.join(halo_directory,'executables','consistent-trees')
    tree_config_file = os.path.join(workpath,'catalog/outputs/merger_tree.cfg')


    # generate merger tree config file (catalog/outputs/merger_tree.cfg) from rockstar config file
    # os.system(f'perl {rockstar_directory}/scripts/gen_merger_cfg.pl catalog/rockstar.cfg')

    fn = os.system if run else print
    if len(os.listdir(os.path.join(workpath,'catalog','trees'))) > 0: 
        print("<<<< Already produced consistent-trees trees, skipping <submit_consistent_trees.0> >>>>")
        fn = print

    # print run-time and CPU information
    ScriptPrint = ut_io.SubmissionScriptClass('slurm')

    # generate tree files
    # assume non-periodic boundaries
    fn(
        f'perl {consistentrees_directory}/do_merger_tree_np.pl'
        + f' {consistentrees_directory} {tree_config_file}'
    )
    # assume periodic boundaries
    # os.system('perl {}/do_merger_tree.pl {} {}'.format(
    #    consistentrees_directory, consistentrees_directory, tree_config_file))

    fn = os.system if run else print
    scalefile = None
    with open(tree_config_file,'r') as handle:
        for line in handle.readlines():
            if 'SCALEFILE' in line: scalefile = line.split('=')[-1].replace(' ','').replace('\n','').replace('"','')

    n_hlists = -1
    with open(scalefile,'r') as handle:
        lines = handle.readlines()
        n_hlists = len(lines)
    if len(os.listdir(os.path.join(workpath,'catalog','hlists'))) == n_hlists: 
        print("<<<< Already produced consistent-trees hlists, skipping <submit_consistent_trees.1> >>>>")
        fn = print
    #else: print(len(os.listdir(os.path.join(workpath,'catalog','hlists'))),n_hlists)

    # generate halo progenitor (hlist) catalogs from trees
    fn(
        f'perl {consistentrees_directory}/halo_trees_to_catalog.pl'
        + f' {consistentrees_directory} {tree_config_file}'
    )

    # print run-time information
    if fn is not print: ScriptPrint.print_runtime()
    #time.sleep(2)

def submit_hdf5(workpath,snapshot_indices,run=False):
    #time.sleep(2)

    last_fname = os.path.join(workpath,'catalog_hdf5',f'halo_{snapshot_indices[-1]:03d}.hdf5')
    tree_fname = os.path.join(workpath,'catalog_hdf5','tree.hdf5')

    if os.path.isfile(last_fname) and os.path.isfile(tree_fname):
        print("<<<< Already converted catalogs to hdf5, skipping <submit_hdf5> >>>>")
        run = False

    if run: 
        # print run-time and CPU information
        ScriptPrint = ut_io.SubmissionScriptClass('slurm')

        ## move to the workpath in case we're not there
        os.chdir(workpath)

        # assume am in rockstar directory
        current_directory = os.getcwd().split('/')
        rockstar_directory = current_directory[-2] + '/' + current_directory[-1]
    
        halo_io.IO.rewrite_as_hdf5('../../', rockstar_directory)

        # print run-time information
        ScriptPrint.print_runtime()

    #time.sleep(2)

def submit_particle(
    species_name, # particle species to assign
    snapshot_indices,
    run=False): # default snapshot selection

    last_fname = os.path.join(os.getcwd(),'catalog_hdf5',f'star_{snapshot_indices[-1]:03d}.hdf5')
    if os.path.isfile(last_fname):
        print("<<<< Already assigned stars to halos, skipping <submit_particle> >>>>")
        run = False

    if run:
        # print run-time and CPU information
        ScriptPrint = ut_io.SubmissionScriptClass('slurm')

        print(f'assigning {species_name} particles to halos at indices: {snapshot_indices}')
        os.sys.stdout.flush()

        Particle = halo_io.ParticleClass()

        Particle.write_catalogs_with_species(
            species_name, 'index', snapshot_indices, proc_number=ScriptPrint.mpi_number
        )

        # print run-time information
        ScriptPrint.print_runtime()
    #time.sleep(2)
