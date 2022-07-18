# rockstar_abg
some wrappers around andrew wetzel's incredible collection of rockstar repositories


"installation" instructions:

```bash
git clone git@github.com:agurvich/rockstar_abg.git
cd rockstar_abg
git submodule init
git submodule update
python setup.py install #<— may need to link C libraries like hdf5 if you haven’t already. Will unzip modifications on top of Andrew’s code and compile necessary C code
```

This will unzip modifications to Andrew's code (mostly just making it use relative imports rather than absolute-- also one change to a Makefile to use gcc rather than icc). 

Then you should be able to call `runner.py` as is done in `job_maker.sh` to generate halo files in the simulation directory.
