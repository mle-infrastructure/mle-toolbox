import torch
import copy
import argparse
import commentjson
import os
import yaml
import json
import numpy as np
import h5py
import pickle
import platform
import re
import mle_toolbox.cluster_config as cc


def determine_resource():
    """ Check if cluster (sge/slurm) is available or only local run. """
    hostname = platform.node()
    on_sge_cluster = any(re.match(l, hostname) for l in cc.sge_node_reg_exp)
    on_slurm_cluster = any(re.match(l, hostname) for l in cc.slurm_node_reg_exp)
    on_sge_head = (hostname in cc.sge_head_names)
    on_slurm_head = (hostname in cc.slurm_head_names)
    if on_sge_head or on_sge_cluster:
        return "sge-cluster"
    elif on_slurm_head or on_slurm_cluster:
        return "slurm-cluster"
    else:
        return hostname


def print_framed(str_to_print: str, line_width: int=85):
    """ Add === x === around your string to print. """
    left = np.ceil((line_width-len(str_to_print))/2).astype("int") - 2
    right = np.floor((line_width-len(str_to_print))/2).astype("int") - 2
    print(left*"=" + "  " + str_to_print + "  " + right*"=")


class DotDic(dict):
    """ Helper to load in parameters from json & easily call them """
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __deepcopy__(self, memo=None):
        return DotDic(copy.deepcopy(dict(self), memo=memo))


class NpEncoder(json.JSONEncoder):
    """ Small Helper Encoder to convert np ints into int & dump """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def get_configs_ready(default_seed: int=0,
                      default_config_fname: str="configs/base_config.json",
                      default_experiment_dir: str="experiments/"):
    """ Prepare the config files for the experiment run. """
    def get_cmd_args():
        """ Get env name, config file path & device to train from cmd line """
        parser = argparse.ArgumentParser()
        # Standard inputs for all training runs
        parser.add_argument('-config', '--config_fname', action="store",
                            default=default_config_fname, type=str,
                            help='Filename from which to load config')
        parser.add_argument('-exp_dir', '--experiment_dir', action="store",
                            default=default_experiment_dir, type=str,
                            help='Directory to store logs in.')

        # Command line input for the random seed to replicate experiment
        parser.add_argument('-seed', '--seed_id', action="store",
                            default=default_seed, type=int,
                            help='Seed id on which to train')

        # Special command line inputs for cross-validation
        parser.add_argument('-fold_id', '--cv_fold_id', action="store",
                            help='Fold id on which to train')
        parser.add_argument('-fold_path', '--cv_fold_path', action="store",
                            help='Paths to sample fold ids in .npy')
        return parser.parse_args()

    cmd_args = get_cmd_args()
    # Load config file + add config fname to clone + add experiment dir
    config = load_config(cmd_args.config_fname)
    config.log_config.config_fname = cmd_args.config_fname
    config.log_config.experiment_dir = cmd_args.experiment_dir

    net_config = DotDic(config["net_config"])
    train_config = DotDic(config["train_config"])
    log_config = DotDic(config["log_config"])

    # Add device to train on if not already set in the config file
    if train_config.device_name is None:
        train_config.device_name = "cuda" if torch.cuda.is_available() else "cpu"

    if log_config.tboard_fname is None and log_config.use_tboard:
        tboard_temp = os.path.split(cmd_args.config_fname)[1]
        tboard_base = os.path.splitext(tboard_temp)[0]
        log_config.tboard_fname = tboard_base

    # Set seed for run of your choice - has to be done via command line
    train_config.seed_id = cmd_args.seed_id
    log_config.fname_ext = "seed-" + str(cmd_args.seed_id)

    # Set the cross-validation fold id & path for ids (if applicable)
    if cmd_args.cv_fold_id is not None:
        train_config.fold_id = cmd_args.cv_fold_id
        train_config.fold_path = cmd_args.cv_fold_path
        log_config.fname_ext = "fold-" + str(cmd_args.cv_fold_id)

    return train_config, net_config, log_config


def load_config(config_fname: str):
    """ Load in a config JSON file and return as a dictionary """
    json_config = commentjson.loads(open(config_fname, 'r').read())
    dict_config = DotDic(json_config)

    # Make inner dictionaries indexable like a class
    for key, value in dict_config.items():
        if isinstance(value, dict):
            dict_config[key] = DotDic(value)
    return dict_config


def load_yaml_config(config_fname: str) -> dict:
    """ Load in a YAML config file & wrap as DotDic. """
    with open(config_fname) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return DotDic(config)


def save_pkl_object(obj, filename):
    """ Helper to store pickle objects """
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def load_pkl_object(filename):
    """ Helper to reload pickle objects """
    with open(filename, 'rb') as input:
        obj = pickle.load(input)
    return obj


def load_log(log_fname: str, mean_over_seeds: bool=True,
             mean_also_evals: bool=False) -> DotDic:
    """ Load in logging results & mean the results over different runs """
    # Open File & Get array names to load in
    h5f = h5py.File(log_fname, mode="r")
    run_names = list(h5f.keys())
    run_ids = list(set([r_n[:-17] for r_n in run_names]))
    obj_names = list(h5f[list(h5f.keys())[0]].keys())

    # Create a group for each random seed in the runs
    if not mean_over_seeds:
        result_dict = {key: {} for key in run_names}
        for j in range(len(run_names)):
            data_to_store = [[] for i in range(len(obj_names))]
            run = h5f[run_names[j]]
            for i, o_name in enumerate(obj_names):
                data_to_store[i].append(run[o_name][:])

            result_sub = {key: {} for key in obj_names}
            # Loop over runs and construct the results individually
            for i, o_name in enumerate(obj_names):
                result_dict[run_names[j]][o_name] = data_to_store[i][0]
        h5f.close()
        if len(run_names) == 1:
            result_dict = result_dict[list(result_dict.keys())[0]]

    # Mean over the groups
    if mean_over_seeds:
        result_dict = {key: {} for key in run_ids}
        # Getting group of seeds by configs
        run_selectors = []
        for run_id in run_ids:
            select = []
            for f in run_names:
                if run_id in f:
                    select.append(f)
            run_selectors.append(select)

        # Open up file again & collect data in one group to mean over!
        h5f = h5py.File(log_fname, mode="r")
        for i, run_id in enumerate(run_ids):
            data_to_store = [[] for i in range(len(obj_names))]
            for seed_id in run_selectors[i]:
                run = h5f[seed_id + "/"]
                for i, o_name in enumerate(obj_names):
                    data_to_store[i].append(run[o_name][:])

            mean_dict = {key: {} for key in obj_names}
            # Get maximum length of stored logs!
            length_of_ts = [data_to_store[0][i].shape[0] for i in range(len(data_to_store[0]))]
            min_entries = np.min(length_of_ts)

            # Post process results - Mean over different runs
            for i, o_name in enumerate(obj_names):
                stack_data = [data_to_store[i][j][:min_entries] for j in range(len(data_to_store[0]))]
                mean_dict[o_name]["mean"] = np.mean(stack_data, axis=0)
                mean_dict[o_name]["std"] = np.std(stack_data, axis=0)
            result_dict = mean_dict
        h5f.close()
    # Return as dot-callable dictionary
    if mean_also_evals:
        result_dict = mean_over_evals(result_dict)
    return DotDic(result_dict)


def mean_over_evals(result_dict):
    """ Mean all individual runs over their respective seeds. """
    all_keys = list(result_dict.keys())
    eval_runs, seeds = [], []
    split_by = "_seed-" if "seed" in all_keys[0] else "_fold-"
    for i in range(len(all_keys)):
        split = all_keys[i].split(split_by)
        eval_runs.append(split[0])
        seeds.append(split[1])

    unique_runs = list(set(eval_runs))
    unique_seeds = list(set(seeds))

    new_results_dict = {}

    for run in unique_runs:
        all_seeds_for_run = [i for i in all_keys if i.startswith(run + "_")]
        obj_names = list(result_dict[all_seeds_for_run[0]].keys())
        mean_dict = {key: {} for key in obj_names}
        data_to_store = [[] for i in range(len(obj_names))]

        for i, seed_id in enumerate(all_seeds_for_run):
            seed_run = result_dict[seed_id]
            for i, o_name in enumerate(obj_names):
                data_to_store[i].append(seed_run[o_name][:])

            mean_dict = {key: {} for key in obj_names}
            # Post process results - Mean over different runs
        for i, o_name in enumerate(obj_names):
            mean_tol, std_tol = tolerant_mean(data_to_store[i])
            mean_dict[o_name]["mean"] = mean_tol
            mean_dict[o_name]["std"] = std_tol

        new_results_dict[run] = mean_dict

    return new_results_dict


def tolerant_mean(arrs):
    """ Helper function for case where data to mean has different lengths. """
    lens = [len(i) for i in arrs]
    arr = np.ma.empty((np.max(lens),len(arrs)))
    arr.mask = True
    for idx, l in enumerate(arrs):
        arr[:len(l),idx] = l
    return arr.mean(axis = -1), arr.std(axis=-1)
