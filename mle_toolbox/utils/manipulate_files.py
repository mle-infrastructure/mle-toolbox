import os
from typing import List, Union
import pickle
import h5py
import yaml
import copy
import numpy as np
import pandas as pd
from .general import DotDic


def load_pkl_object(filename: str):
    """ Helper to reload pickle objects """
    with open(filename, 'rb') as input:
        obj = pickle.load(input)
    return obj


def merge_hdf5_files(new_filename: str,
                     log_paths: List[str],
                     file_ids: Union[None, List[str]] = None,
                     delete_files: bool = False):
    """ Merges a set of hdf5 files into a new hdf5 file with more groups. """
    file_to = h5py.File(new_filename, 'w')
    for i, log_p in enumerate(log_paths):
        file_from = h5py.File(log_p,'r')
        datasets = get_datasets('/', file_from)
        if file_ids is None:
            write_data_to_file(file_to, file_from, datasets)
        else:
            # Maintain unique config id even if they have same random seed
            write_data_to_file(file_to, file_from, datasets, file_ids[i])
        file_from.close()

        # Delete individual log file if desired
        if delete_files:
            os.remove(log_p)
    file_to.close()


def get_datasets(key: str,
                 archive: h5py.File):
    """ Collects different paths to datasets in recursive fashion. """
    if key[-1] != '/': key += '/'
    out = []
    for name in archive[key]:
        path = key + name
        if isinstance(archive[path], h5py.Dataset):
            out += [path]
        else:
            out += get_datasets(path, archive)
    return out


def write_data_to_file(file_to: h5py.File,
                       file_from: h5py.File,
                       datasets: List[str],
                       file_id: Union[str, None] = None):
    """ Writes the datasets from-to file. """
    # get the group-names from the lists of datasets
    groups = list(set([i[::-1].split('/', 1)[1][::-1] for i in datasets]))
    if file_id is None:
        groups = [i for i in groups if len(i) > 0]
    else:
        groups = [i[0] + file_id + "_" + i[1:] for i in groups if len(i) > 0]
    # sort groups based on depth
    idx    = np.argsort(np.array([len(i.split('/')) for i in groups]))
    groups = [groups[i] for i in idx]

    # create all groups that contain dataset that will be copied
    for group in groups:
        file_to.create_group(group)

    # copy datasets
    for path in datasets:
        # - get group name // - minimum group name // - copy data
        group = path[::-1].split('/',1)[1][::-1]
        if len(group) == 0: group = '/'
        if file_id is not None:
            group_to_index = group[0] + file_id + "_" + group[1:]
        else:
            group_to_index = group
        file_from.copy(path, file_to[group_to_index])

    file_from.close()


def reload_hyper_log(hyper_log_fpath: str):
    """ Reload the previously stored .pkl log file """
    opt_log = load_pkl_object(hyper_log_fpath)
    all_evaluated_params = []
    for key, eval_iter in opt_log.items():
        all_evaluated_params.append(eval_iter["params"])
    return opt_log


def hyper_log_to_df(hyper_log_fpath: str):
    """ Load & transform the dictionary log into a pandas df"""
    # Load the log from the pkl file
    hyper_log = reload_hyper_log(hyper_log_fpath)

    hyper_list = []
    list_of_run_dicts = [hyper_log[i] for i in hyper_log.keys()]

    def merge_two_dicts(x: dict, y: dict):
        """Given two dicts, merge them into new dict as shallow copy."""
        z = x.copy()
        z.update(y)
        return z

    for i in range(len(list_of_run_dicts)):
        # Unpack the individual params dictionaries for better indexing
        unravel_params = merge_two_dicts(list_of_run_dicts[i]["params"], list_of_run_dicts[i])
        del unravel_params["params"]
        hyper_list.append(unravel_params)
    # Put list of dicts into pandas df
    hyper_df = pd.DataFrame(hyper_list)
    return hyper_df
