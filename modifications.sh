#!/bin/bash

zip modifications.zip \
src/rockstar_abg/gizmo_analysis/gizmo_agetracer.py \
src/rockstar_abg/gizmo_analysis/gizmo_diagnostic.py \
src/rockstar_abg/gizmo_analysis/gizmo_file.py \
src/rockstar_abg/gizmo_analysis/gizmo_group.py \
src/rockstar_abg/gizmo_analysis/gizmo_ic.py \
src/rockstar_abg/gizmo_analysis/gizmo_io.py \
src/rockstar_abg/gizmo_analysis/gizmo_plot.py \
src/rockstar_abg/gizmo_analysis/gizmo_star.py \
src/rockstar_abg/gizmo_analysis/gizmo_track.py \
src/rockstar_abg/utilities/io.py \
src/rockstar_abg/halo_analysis/halo_plot.py \
src/rockstar_abg/halo_analysis/halo_select.py \
src/rockstar_abg/halo_analysis/halo_io.py \
src/rockstar_abg/executables/rockstar-galaxies/Makefile \
src/rockstar_abg/executables/rockstar-galaxies-fire2/Makefile \
src/rockstar_abg/executables/rockstar-galaxies-fire2/io/io_gizmo.c \
src/rockstar_abg/executables/rockstar-galaxies-fire2/io/io_gizmo_dm.c

## changes:
## for .py files, change imports to be relative using . | .. | etc...
## for rockstar-galaxies*/Makefile change from icc to gcc
## for rockstar-galaxies-fire2/io_gizmo* remove _ from Omega_Lambda and Omega_Matter
