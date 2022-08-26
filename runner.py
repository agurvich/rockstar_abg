import numpy as np
import sys

from abg_python.function_utils import CLI_args

from rockstar_abg.handler import main as handler

@CLI_args()
def main(sim_path=None,name='m12m_m6e4',suite_name='fire3_compatability/core'):

    try: 
        handler(
            name,
            sim_path,
            suite_name,
            snapshot_indices = None, ## use all snapshots in output directory
            run=True)
    except Exception as e:
        print(e.args)
        raise

if __name__ == '__main__':
    main()
