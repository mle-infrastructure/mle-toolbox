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
from typing import Union, List
from dotmap import DotMap


def load_mle_toolbox_config():
    """ Load cluster config from the .toml file. See docs for more info. """
    return DotMap(toml.load(os.path.expanduser("~/mle_config.toml")),
                  _dynamic=False)


def load_yaml_config(cmd_args: dict) -> DotMap:
    """ Load in a YAML config file & wrap as DotMap. """
    with open(cmd_args.config_fname) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # Update job config with specific cmd args (if provided)
    config = overwrite_config_with_args(config, cmd_args)
    return DotMap(config, _dynamic=False)


def load_json_config(config_fname: str) -> DotMap:
    """ Load in a config JSON file and return as a dictionary """
    json_config = commentjson.loads(open(config_fname, 'r').read())
    dict_config = DotMap(json_config, _dynamic=False)
    return dict_config


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
    """ Helper to store pickle objects. """
    with open(filename, 'wb') as output:
        # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def load_pkl_object(filename):
    """ Helper to reload pickle objects. """
    with open(filename, 'rb') as input:
        obj = pickle.load(input)
    return obj


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


def print_framed(str_to_print: str,
                 line_width: int=85,
                 frame_str: str = "="):
    """ Add === x === around your string to print. """
    left = np.ceil((line_width-len(str_to_print))/2).astype("int") - 2
    right = np.floor((line_width-len(str_to_print))/2).astype("int") - 2
    print(left*frame_str + "  " + str_to_print + "  " + right*frame_str)


def get_jax_os_ready(num_devices: int=1,
                     num_threads: int=1,
                     mem_prealloc_bool: bool=False,
                     mem_prealloc_fraction: float=0.9,
                     device_type: str="cpu"):
    """ Helper to set up os variables for JAX/XLA experiment. """
    # Set number of devices (CPU cores/GPUs/TPUs) - helps with pmap testing
    os.environ['XLA_FLAGS'] = f'--xla_force_host_platform_device_count={num_devices}'
    # TODO: Set threads for XLA multithreading
    if device_type == "cpu":
        os.environ["XLA_FLAGS"] += os.pathsep + (
                                  "--xla_cpu_multi_thread_eigen=false "
                                  "intra_op_parallelism_threads={num_threads}")
    # Set environment variables for memory preallocation on GPU
    elif device_type == "gpu":
        os.environ['XLA_PYTHON_CLIENT_PREALLOCATE'] = mem_prealloc_bool
        os.environ['XLA_PYTHON_CLIENT_MEM_FRACTION'] = f'{memory_prealloc_fraction}'
    # Set environment variables for TPU usage
    # TODO: This only works for colab (?) - need to install jaxlib version!
    # Tackle this once I get to automated GCP setup!
    elif device_type == "tpu":
        import jax.tools.colab_tpu
        jax.tools.colab_tpu.setup_tpu()
    return
