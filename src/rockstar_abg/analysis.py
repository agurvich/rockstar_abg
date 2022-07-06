import numpy as np

from rockstar_abg.halo_analysis.halo_io import IOClass


def get_tree(pathh,which_halo=0):
    IOhandler = IOClass()
    tree = IOhandler.read_tree(pathh)

    if which_halo != 0: raise NotImplementedError("Not sure if the below actually works for other halos")
    ## find the end of the progenitor list which ends up in the first final halo
    #halo_index = np.argmin(tree['final.index'] == tree['final.index'][0])
    halo_index = tree['progenitor.last.dindex'][which_halo]+1
    ## gather indices splitting snapshots (do this by finding the unique)
    ##  values of the indices of the "host" (which is assigned as the most massive halo)
    #splits = np.unique(tree['host.index'][:halo_index])[1:]
    ## ABG: this might not work for halos that aren't the most massive, safer to do it 
    ##  the "slow" way:
    splits = []
    i = 0
    diffs = np.diff(tree['snapshot'][:halo_index])
    while len(diffs[i:]) > 0 and np.min(diffs[i:]) == -1:
        i += 1+np.argmin(diffs[i:])
        splits+=[i]

    return {key:np.array_split(value[:halo_index],splits) for key,value in tree.items()}

def get_catalogs(pathh,tree=None):

    if tree is None: tree = get_tree(pathh)

    snapshot_values = np.unique(tree['descendant.snapshot'])
    snapshot_values = np.sort(snapshot_values[snapshot_values > 0])

    IOhandler = IOClass()
    catalogs = IOhandler.read_catalogs(
        simulation_directory='/projects/b1026/isultan/halos/m12i_fiducial_push/',
        snapshot_value_kind='index',
        snapshot_values=snapshot_values,
        species='',
        all_snapshot_list=False,)
    
def get_ancestry(tree,catalogs,selection_function=None):
    if selection_function is None: selection_function = most_massive_selection_function

    tids = [0]
    for epoch_i,epoch_halos in enumerate(tree['catalog.index'][1:]):
        ## TODO should figure out what prog_index is generally, not just for main halo...
        ##  probably something to do with progenitor.co.dindex?
        ##  should be a function of the most recently added tid
        prog_index = 0 
        ## how many halos in this epoch are a progenitor of our halo?
        n_progenitors = tree['progenitor.number'][epoch_i][prog_index]

        ## select the progenitor we want using the selection function
        ##  from among the progenitors of this epoch that are
        tids += [selection_function(
            ## pass most recent halo catalog
            catalogs[::-1][epoch_i],tids[-1],
            ## pass catalog data for next snapshot
            catalogs[::-1][epoch_i+1],
            ## pass indices of relevant progenitors
            epoch_halos[:n_progenitors],
            ## pass the tree ids corresponding to the n_progenitors
            tree['tid'][epoch_i][:n_progenitors])]

    ## tree indices of the ancestry line-- 
    ##  one index for each snapshot
    ##  linking the specified halo through time
    return tids

def most_massive_selection_function(
    now_catalog,
    halo_index,
    epoch_catalog,
    prog_indices,
    tids):

    ## choose the most massive halo
    return tids[np.argmax([epoch_catalog['mass'][prog_index] for prog_index in prog_indices])]

def min_phase_space_dist(
    now_catalog,
    halo_index,
    epoch_catalog,
    prog_indices,
    prog_tids,
    dT=None):

    phase_dists = np.zeros(prog_indices.size)

    ## find distance in log mass space for each progenitor
    phase_dists += [
        np.log10(epoch_catalog['mass'][prog_index]/now_catalog['mass'][halo_index])**2 
        for prog_index in prog_indices]
    
    ## find distance in physical space for each progenitor, 
    ##  extrapolating the position from the epoch catalog
    if dT is not None:
        phase_dists += [
            np.sum((
                epoch_catalog['position'][prog_index] + 
                epoch_catalog['velocity'][prog_index]*dT -
                now_catalog['position'][halo_index])**2,axis=1)
                for prog_index in prog_indices]

    ## choose the tid corresponding to the minimum phase distance
    return prog_tids[np.argmin(phase_dists)]