import argparse
import commentjson
import os
import yaml
import copy
import json
import toml
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
        log_config.seed_id = "seed_" + str(train_config.seed_id)
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
    with open(filename, 'wb') as output:
        # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def load_pkl_object(filename):
    """ Helper to reload pickle objects """
    with open(filename, 'rb') as input:
        obj = pickle.load(input)
    return obj
