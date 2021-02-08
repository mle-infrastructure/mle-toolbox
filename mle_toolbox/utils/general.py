import argparse
import commentjson
import os
import yaml
import copy
import json
import toml
import h5py
import pickle
import platform
import re
import numpy as np
import random
from typing import Union, List
import pandas as pd
from dotmap import DotMap


try:
    import torch
    __torch_installed = True
except ImportError:
    __torch_installed = False
    pass

try:
    import gym
    __gym_installed = True
except ImportError:
    __gym_installed = False
    pass

try:
    import jax
    __jax_installed = True
except ImportError:
    __jax_installed = False
    pass


def load_mle_toolbox_config():
    """ Load cluster config from the .toml file. See docs for more info. """
    return DotMap(toml.load(os.path.expanduser("~/mle_config.toml")),
                  _dynamic=False)


def determine_resource():
    """ Check if cluster (sge/slurm) is available or only local run. """
    cc = load_mle_toolbox_config()
    hostname = platform.node()
    on_sge_cluster = any(re.match(l, hostname) for
                         l in cc.sge.info.node_reg_exp)
    on_slurm_cluster = any(re.match(l, hostname) for
                           l in cc.slurm.info.node_reg_exp)
    on_sge_head = (hostname in cc.sge.info.head_names)
    on_slurm_head = (hostname in cc.slurm.info.head_names)
    if on_sge_head or on_sge_cluster:
        return "sge-cluster"
    elif on_slurm_head or on_slurm_cluster:
        return "slurm-cluster"
    else:
        return hostname


def print_framed(str_to_print: str, line_width: int=85,
                 frame_str: str = "="):
    """ Add === x === around your string to print. """
    left = np.ceil((line_width-len(str_to_print))/2).astype("int") - 2
    right = np.floor((line_width-len(str_to_print))/2).astype("int") - 2
    print(left*frame_str + "  " + str_to_print + "  " + right*frame_str)


def set_random_seeds(seed_id: Union[int, None], return_key: bool=False,
                     verbose: bool=False):
    """ Set random seed (random, npy, torch, gym) for reproduction """
    if seed_id is not None:
        os.environ['PYTHONHASHSEED'] = str(seed_id)
        random.seed(seed_id)
        np.random.seed(seed_id)
        seeds_set = ['random', 'numpy']
        if __torch_installed:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            torch.manual_seed(seed_id)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed_id)
                torch.cuda.manual_seed(seed_id)
            seeds_set.append('torch')

        if __gym_installed:
            if hasattr(gym.spaces, 'prng'):
                gym.spaces.prng.seed(seed_id)
            seeds_set.append('gym')

        if verbose:
            print(f"-- Random seeds ({', '.join(seeds_set)}) were set to {seed_id}")

        if return_key:
            if not __jax_installed:
                raise ValueError("You need to install jax to return a PRNG key.")
            key = jax.random.PRNGKey(seed_id)
            return key
    else:
        print("Please provide seed_id that is not None. Using package default.")


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


def get_configs_ready(default_seed: Union[None, int] = None,
                      default_config_fname: str="configs/base_config.json",
                      default_experiment_dir: str="experiments/"):
    """ Prepare the config files for the experiment run. """
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
                        default=default_seed,
                        help='Seed id on which to train')
    cmd_args = parser.parse_args()

    # Load config file + add config fname to clone + add experiment dir
    config = load_config(cmd_args.config_fname)
    config.log_config.config_fname = cmd_args.config_fname
    config.log_config.experiment_dir = cmd_args.experiment_dir

    net_config = DotMap(config["net_config"], _dynamic=False)
    train_config = DotMap(config["train_config"], _dynamic=False)
    log_config = DotMap(config["log_config"], _dynamic=False)

    # Add device to train on if not already set in the config file
    if "device_name" in train_config.keys():
        device_name = "cpu"
        if __torch_installed and torch.cuda.is_available():
            device_name = "cuda"
        train_config.device_name = device_name

    if "tboard_fname" not in log_config.keys():
        if "use_tboard" in log_config.keys():
            if log_config.use_tboard:
                tboard_temp = os.path.split(cmd_args.config_fname)[1]
                tboard_base = os.path.splitext(tboard_temp)[0]
                log_config.tboard_fname = tboard_base

    # Set seed for run of your choice - has to be done via command line
    if cmd_args.seed_id is not None:
        train_config.seed_id = int(cmd_args.seed_id)
        log_config.seed_id = "seed_" + str(cmd_args.seed_id)
    else:
        log_config.seed_id = "seed_not_set"
    return train_config, net_config, log_config


def load_config(config_fname: str):
    """ Load in a config JSON file and return as a dictionary """
    json_config = commentjson.loads(open(config_fname, 'r').read())
    dict_config = DotMap(json_config, _dynamic=False)
    return dict_config


def load_yaml_config(cmd_args: dict) -> dict:
    """ Load in a YAML config file & wrap as DotMap. """
    with open(cmd_args.config_fname) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # Update job config with additional cmd args (if provided)
    config = overwrite_config_with_args(config, cmd_args)
    return DotMap(config, _dynamic=False)


def overwrite_config_with_args(config, cmd_args):
    """ Update entries if there was command line input. """
    if cmd_args.base_train_fname is not None:
        config["meta_job_args"]["base_train_fname"] = cmd_args.base_train_fname
    if cmd_args.base_train_config is not None:
        config["meta_job_args"]["base_train_config"] = cmd_args.base_train_config
    if cmd_args.experiment_dir is not None:
        config["meta_job_args"]["experiment_dir"] = cmd_args.experiment_dir
    return config


def save_pkl_object(obj, filename):
    """ Helper to store pickle objects """
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def load_pkl_object(filename):
    """ Helper to reload pickle objects """
    with open(filename, 'rb') as input:
        obj = pickle.load(input)
    return obj


def load_log(log_fname: str, mean_seeds: bool=True) -> DotMap:
    """ Load in logging results & mean the results over different runs """
    # Open File & Get array names to load in
    h5f = h5py.File(log_fname, mode="r")
    # Get all ids of all runs (b_1_eval_0_seed_0)
    run_names = list(h5f.keys())
    # Get only stem of ids (b_1_eval_0)
    run_ids = list(set([r_n.split("_seed")[0] for r_n in run_names]))
    # Get all main data source keys ("meta", "stats", "time")
    data_sources = list(h5f[run_names[0]].keys())
    # Get all variables within the data sources
    data_items = {data_sources[i]:
                  list(h5f[run_names[0]][data_sources[i]].keys())
                  for i in range(len(data_sources))}

    # Create a group for each runs (eval and seed)
    # Out: {'b_1_eval_0_seed_0': {'meta': {}, 'stats': {}, 'time': {}}, ...}
    result_dict = {key: {} for key in run_names}
    for rn in run_names:
        run = h5f[rn]
        source_to_store = {key: {} for key in data_sources}
        for ds in data_sources:
            run_source = run[ds]
            data_to_store = {key: {} for key in data_items[ds]}
            for i, o_name in enumerate(data_items[ds]):
                data_to_store[o_name] = run[ds][o_name][:]
            source_to_store[ds] = data_to_store
        result_dict[rn] = source_to_store
    h5f.close()

    # Return as dot-callable dictionary
    if mean_over_seeds:
        result_dict = mean_over_seeds(result_dict)
    return DotMap(result_dict, _dynamic=False)


def mean_over_seeds(result_dict: DotMap) -> DotMap:
    """ Mean all individual runs over their respective seeds.
        IN: {'b_1_eval_0_seed_0': {'meta': {}, 'stats': {}, 'time': {}},
             'b_1_eval_0_seed_1': {'meta': {}, 'stats': {}, 'time': {}},
              ...}
        OUT: {'b_1_eval_0': {'meta': {}, 'stats': {}, 'time': {},
              'b_1_eval_1': {'meta': {}, 'stats': {}, 'time': {}}
    """
    all_runs = list(result_dict.keys())
    eval_runs = []
    split_by = "_seed_"

    # Get again the different unique runs (without their seeds)
    for run in all_runs:
        split = run.split(split_by)
        eval_runs.append(split[0])
    unique_evals = list(set(eval_runs))

    # Get seeds specific to each one of eval/run - append later on to meta data
    evals_and_seeds = {key: [] for key in unique_evals}
    for run in all_runs:
        split = run.split(split_by)
        evals_and_seeds[split[0]].append(int(split[1]))

    # Loop over all evals (e.g. b_1_eval_0) and merge + aggregate data
    new_results_dict = {}
    for eval in unique_evals:
        all_seeds_for_run = [i for i in all_runs if i.startswith(eval + "_")]
        data_temp = result_dict[all_seeds_for_run[0]]
        # Get all main data source keys ("meta", "stats", "time")
        data_sources = list(data_temp.keys())
        # Get all variables within the data sources
        data_items = {data_sources[i]:
                      list(data_temp[data_sources[i]].keys())
                      for i in range(len(data_sources))}

        # Collect all runs together - data at this point is not modified
        source_to_store = {key: {} for key in data_sources}
        for ds in data_sources:
            data_to_store = {key: [] for key in data_items[ds]}
            for i, o_name in enumerate(data_items[ds]):
                for i, seed_id in enumerate(all_seeds_for_run):
                    seed_run = result_dict[seed_id]
                    data_to_store[o_name].append(seed_run[ds][o_name][:])
            source_to_store[ds] = data_to_store
        new_results_dict[eval] = source_to_store

        # Aggregate over the collected runs
        mean_sources = {key: {} for key in data_sources}
        for ds in data_sources:
            # Mean over time and stats data
            if ds in ["time", "stats"]:
                mean_dict = {key: {} for key in data_items[ds]}
                for i, o_name in enumerate(data_items[ds]):
                    mean_tol, std_tol = tolerant_mean(new_results_dict[eval][ds][o_name])
                    mean_dict[o_name]["mean"] = mean_tol
                    mean_dict[o_name]["std"] = std_tol
            # Append over all meta data (strings, seeds nothing to mean)
            elif ds == "meta":
                mean_dict = {}
                for i, o_name in enumerate(data_items[ds]):
                    temp = np.array(
                    new_results_dict[eval][ds][o_name]).squeeze().astype('U200')
                    # Get rid of duplicate experiment dir strings
                    if o_name in ["experiment_dir", "eval_id"]:
                        mean_dict[o_name] = str(np.unique(temp)[0])
                    else:
                        mean_dict[o_name] = temp

                # Add seeds as clean array of integers to dict
                mean_dict["seeds"] = {}
                mean_dict["seeds"] = evals_and_seeds[eval]
            else:
                raise ValueError
            mean_sources[ds] = mean_dict
        new_results_dict[eval] = mean_sources
    return DotMap(new_results_dict, _dynamic=False)


def tolerant_mean(arrs: list):
    """ Helper function for case where data to mean has different lengths. """
    lens = [len(i) for i in arrs]
    arr = np.ma.empty((np.max(lens),len(arrs)))
    arr.mask = True
    for idx, l in enumerate(arrs):
        arr[:len(l),idx] = l
    return arr.mean(axis = -1), arr.std(axis=-1)


def get_closest_sub_df(df: pd.core.frame.DataFrame,
                       param_name: Union[List[str], str],
                       param_value: Union[List[float], int, float]):
    """ Return df with fixed params closest to param_value in df. """
    # Make sure to iterate over list of parameters + copy the df
    if type(param_name) != list:
        param_name = [param_name]
    if type(param_value) != list:
        param_value = [param_value]
    sub_df = df.copy()

    # Loop over parameters and construct the sub-df
    for i, name in enumerate(param_name):
        all_values = df[name].unique()
        min_id = np.argmin(np.abs(all_values - param_value[i]))
        sub_df = sub_df[sub_df[name] == all_values[min_id]]
    return sub_df


def subselect_meta_log(meta_log: DotMap, run_ids: List[str]):
    """ Subselect the meta log dict based on run id list. """
    sub_log = DotMap()
    for run_id in run_ids:
        sub_log[run_id] = meta_log[run_id]
    return sub_log
