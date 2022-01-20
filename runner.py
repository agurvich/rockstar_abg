import numpy as np

from rockstar_abg.handler import main as handler

def main():
    handler(
        'm12i_m6e4',
        'fire3_compatability/core',
        snapshot_indices = np.arange(0,61),
        run=True,
        )

if __name__ == '__main__':
    main()
