import os
import glob
import subprocess

from .utilities import io as ut_io
from .gizmo_analysis import gizmo_io

def submit_rockstar(rockstar_directory=None,run=False):

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

        config_file_name = os.path.join(rockstar_directory,config_file_name)

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

def submit_consistent_trees(workpath,halo_directory,run=False):
    # directories and files
    if halo_directory is None:
        halo_directory = os.environ['HOME'] + '/local/halo/'

    rockstar_directory = os.path.join(halo_directory,'executables','rockstar-galaxies')
    consistentrees_directory = os.path.join(halo_directory,'executables','consistent-trees')
    tree_config_file = os.path.join(workpath,'catalog/outputs/merger_tree.cfg')

    # print run-time and CPU information
    ScriptPrint = ut_io.SubmissionScriptClass('slurm')

    # generate merger tree config file (catalog/outputs/merger_tree.cfg) from rockstar config file
    # os.system(f'perl {rockstar_directory}/scripts/gen_merger_cfg.pl catalog/rockstar.cfg')


    fn = os.system if run else print

    # generate tree files
    # assume non-periodic boundaries
    fn(
        f'perl {consistentrees_directory}/do_merger_tree_np.pl'
        + f' {consistentrees_directory} {tree_config_file}'
    )
    # assume periodic boundaries
    # os.system('perl {}/do_merger_tree.pl {} {}'.format(
    #    consistentrees_directory, consistentrees_directory, tree_config_file))
    ## TODO consider removing
    os.chdir(consistentrees_directory)

    # generate halo progenitor (hlist) catalogs from trees
    fn(
        f'perl {consistentrees_directory}/halo_trees_to_catalog.pl'
        + f'  {tree_config_file} {consistentrees_directory}'
    )

    # print run-time information
    ScriptPrint.print_runtime()
