import os
import glob

from .utilities import io as ut_io
from .gizmo_analysis import gizmo_io

FIREPATH = '/scratch/projects/xsede/GalaxiesOnFIRE'

def main(savename,suite_name='fire3_compatability/core'):

    workpath = os.path.join(
        FIREPATH,
        suite_name,
        savename)
    
    run_rockstar(workpath)

def run_rockstar(workpath):

    ## step 1

    ## make halo directories if necessary
    ## step 3
    make_halo_dirs(workpath)

    ## step 4
    ## mimic submitting from directory
    current_dir = os.path.dirname(__file__)
    os.chdir(os.path.join(workpath,'halo','rockstar_dm'))
    submit_rockstar(current_dir+os.sep)

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

    executable_file_name = os.path.join(
        halo_directory,
        'executables',
        'rockstar-galaxies')
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

        config_file_name = halo_directory + config_file_name

    
    if not run:
        print("Running from",os.getcwd())
    fn = os.system if run else print
    # start server
    fn(f'{executable_file_name} -c {config_file_name} &')

    # start worker
    fn(
        f'ibrun mem_affinity {executable_file_name} -c {catalog_directory}auto-rockstar.cfg'
        + ' >> rockstar_jobs/rockstar_log.txt'
    )

    SubmissionScript.print_runtime()