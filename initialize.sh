#!/bin/bash

git submodule add --force git@bitbucket.org:awetzel/halo_submit.git reference/halo_submit
git submodule add --force git@bitbucket.org:awetzel/consistent-trees.git src/rockstar_abg/executables/consistent-trees
git submodule add --force git@bitbucket.org:awetzel/rockstar-galaxies.git src/rockstar_abg/executables/rockstar-galaxies
git submodule add --force git@bitbucket.org:awetzel/gizmo_analysis.git src/rockstar_abg/gizmo_analysis
git submodule add --force git@bitbucket.org:awetzel/halo_analysis.git src/rockstar_abg/halo_analysis
git submodule add --force git@bitbucket.org:awetzel/utilities.git src/rockstar_abg/utilities
