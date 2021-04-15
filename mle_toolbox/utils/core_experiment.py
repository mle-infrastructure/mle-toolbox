import os
import argparse
import random
import numpy as np
import platform
import re
from typing import Union, List
from dotmap import DotMap
from .core_files_load import load_json_config, load_mle_toolbox_config


# Safely import such that no import errors are thrown - reduce dependencies
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


def set_random_seeds(seed_id: Union[int, None],
                     return_key: bool=False,
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


def get_configs_ready(default_config_fname: str="configs/base_config.json",
                      default_seed: Union[None, int] = None,
                      default_experiment_dir: str="experiments/"):
    """ Prepare job config files for experiment run (add seed id, etc.). """
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

    # Load .json config file + add config fname to clone + add experiment dir
    config = load_json_config(cmd_args.config_fname)
    config.log_config.config_fname = cmd_args.config_fname
    config.log_config.experiment_dir = cmd_args.experiment_dir

    # Subdivide experiment/job config into net, train and log configs
    net_config = DotMap(config["net_config"], _dynamic=False)
    train_config = DotMap(config["train_config"], _dynamic=False)
    log_config = DotMap(config["log_config"], _dynamic=False)

    # Add device to train on if not already set in the config file
    if "device_name" in train_config.keys():
        device_name = "cpu"
        if __torch_installed:
            if torch.cuda.is_available():
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


def determine_resource() -> str:
    """ Check if cluster (sge/slurm) is available. """
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