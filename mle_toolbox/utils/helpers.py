import os
import pickle
from typing import Union, List
import numpy as np


def print_framed(str_to_print: str,
                 line_width: int=85,
                 frame_str: str = "="):
    """ Add === x === around your string to print. """
    left = np.ceil((line_width-len(str_to_print))/2).astype("int") - 2
    right = np.floor((line_width-len(str_to_print))/2).astype("int") - 2
    print(left*frame_str + "  " + str_to_print + "  " + right*frame_str)


def overwrite_config_with_args(config, cmd_args):
    """ Update entries if there was command line input. """
    if cmd_args.base_train_fname is not None:
        config["meta_job_args"]["base_train_fname"] = cmd_args.base_train_fname
    if cmd_args.base_train_config is not None:
        config["meta_job_args"]["base_train_config"] = cmd_args.base_train_config
    if cmd_args.experiment_dir is not None:
        config["meta_job_args"]["experiment_dir"] = cmd_args.experiment_dir
    return config


def save_pkl_object(obj, filename: str):
    """ Helper to store pickle objects. """
    with open(filename, 'wb') as output:
        # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def get_jax_os_ready(num_devices: int=1,
                     num_threads: int=1,
                     mem_prealloc_bool: bool=False,
                     mem_prealloc_frac: float=0.9,
                     device_type: str="cpu"):
    """ Helper to set up os variables for JAX/XLA experiment. """
    # Set number of devices (CPU cores/GPUs/TPUs) - helps with pmap testing
    os.environ['XLA_FLAGS'] = (f'--xla_force_host_platform_device_count'
                               + f'={num_devices}')
    # TODO: Set threads for XLA multithreading
    if device_type == "cpu":
        os.environ["XLA_FLAGS"] += os.pathsep + (
                                  "--xla_cpu_multi_thread_eigen=false "
                                  "intra_op_parallelism_threads={num_threads}")
    # Set environment variables for memory preallocation on GPU
    elif device_type == "gpu":
        os.environ['XLA_PYTHON_CLIENT_PREALLOCATE'] = mem_prealloc_bool
        os.environ['XLA_PYTHON_CLIENT_MEM_FRACTION'] = f'{memory_prealloc_frac}'
    # Set environment variables for TPU usage
    # TODO: This only works for colab (?) - need to install jaxlib version!
    # Tackle this once I get to automated GCP setup!
    elif device_type == "tpu":
        import jax.tools.colab_tpu
        jax.tools.colab_tpu.setup_tpu()
    return
