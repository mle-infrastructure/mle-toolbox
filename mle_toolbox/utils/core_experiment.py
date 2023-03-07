import os
import argparse
import random
import numpy as np
import sys
import select
from typing import Union, Tuple
from dotmap import DotMap
from datetime import datetime
import subprocess as sp
from mle_logging import load_config
from .core_files_load import load_mle_toolbox_config
from .helpers import print_framed


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


# Load in the base toolbox configurations to use throughout
mle_config = load_mle_toolbox_config()


def check_single_job_args(resource_to_run: str, job_arguments: dict):
    """Check if required args are provided. Complete w. default otw."""
    if resource_to_run == "sge-cluster":
        full_job_arguments = sge_check_job_args(job_arguments)
    elif resource_to_run == "slurm-cluster":
        full_job_arguments = slurm_check_job_args(job_arguments)
    elif resource_to_run == "gcp-cloud":
        full_job_arguments = gcp_check_job_args(job_arguments)
    elif resource_to_run == "local":
        full_job_arguments = local_check_job_args(job_arguments)
    else:
        raise ValueError("Please a valid compute resource.")
    return full_job_arguments


def sge_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    if "env_name" not in job_arguments.keys():
        job_arguments["env_name"] = mle_config.general.remote_env_name

    if "use_conda_venv" not in job_arguments.keys():
        job_arguments["use_conda_venv"] = mle_config.general.use_conda_venv

    if "use_venv_venv" not in job_arguments.keys():
        job_arguments["use_venv_venv"] = mle_config.general.use_venv_venv

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.sge.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v

    return job_arguments


def slurm_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    if "env_name" not in job_arguments.keys():
        job_arguments["env_name"] = mle_config.general.remote_env_name

    if "use_conda_venv" not in job_arguments.keys():
        job_arguments["use_conda_venv"] = mle_config.general.use_conda_venv

    if "use_venv_venv" not in job_arguments.keys():
        job_arguments["use_venv_venv"] = mle_config.general.use_venv_venv

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.slurm.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v
    return job_arguments


def gcp_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.gcp.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v

    return DotMap(job_arguments)


# Default job arguments (if not different supplied)
local_default_job_arguments = {
    "env_name": mle_config.general.remote_env_name,
    "use_conda_venv": mle_config.general.use_conda_venv,
    "use_venv_venv": mle_config.general.use_venv_venv,
}


def local_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in local_default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v
    return job_arguments


def load_experiment_config(cmd_args: dict) -> DotMap:
    """Load in YAML config file, overwrite based on cmd & wrap as DotMap."""
    config = load_config(cmd_args.config_fname)

    # Check that meta_job_args and single_job_args given in yaml config
    for k in ["meta_job_args", "single_job_args"]:
        assert k in config.keys(), f"Please provide {k} in .yaml config."

    # Check that job-specific arguments are given in yaml config
    experiment_type = config["meta_job_args"]["experiment_type"]
    all_experiment_types = [
        "single-config",
        "multiple-configs",
        "hyperparameter-search",
        "population-based-training",
    ]
    assert (
        experiment_type in all_experiment_types
    ), f"Job type has to be in {all_experiment_types}."

    if experiment_type == "single-config":
        assert "single_job_args" in config.keys()
    elif experiment_type == "multiple-config":
        assert "multi_config_args" in config.keys()
    elif experiment_type == "hyperparameter-search":
        assert "param_search_args" in config.keys()
    elif experiment_type == "population-based-training":
        assert "pbt_args" in config.keys()

    # Update job config with specific cmd args (if provided)
    if cmd_args.base_train_fname is not None:
        config["meta_job_args"]["base_train_fname"] = cmd_args.base_train_fname
    if cmd_args.base_train_config is not None:
        config["meta_job_args"][
            "base_train_config"
        ] = cmd_args.base_train_config  # noqa: E501
    if cmd_args.experiment_dir is not None:
        config["meta_job_args"]["experiment_dir"] = cmd_args.experiment_dir

    # Check that base_train_fname, base_train_config do exist
    if type(config["meta_job_args"]["base_train_config"]) == str:
        assert os.path.isfile(config["meta_job_args"]["base_train_config"])
    elif type(config["meta_job_args"]["base_train_config"]) == list:
        for train_config in config["meta_job_args"]["base_train_config"]:
            assert os.path.isfile(train_config)
    return DotMap(config, _dynamic=False)


def set_random_seeds(
    seed_id: Union[int, None], return_key: bool = False, verbose: bool = False
):
    """Set random seed (random, npy, torch, gym) for reproduction"""
    if seed_id is not None:
        os.environ["PYTHONHASHSEED"] = str(seed_id)
        random.seed(seed_id)
        np.random.seed(seed_id)
        seeds_set = ["random", "numpy"]
        if __torch_installed:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            torch.manual_seed(seed_id)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed_id)
                torch.cuda.manual_seed(seed_id)
            seeds_set.append("torch")

        if __gym_installed:
            if hasattr(gym.spaces, "prng"):
                gym.spaces.prng.seed(seed_id)
            seeds_set.append("gym")

        if verbose:
            print(f"-- Random seeds ({', '.join(seeds_set)}) set to {seed_id}")

        if return_key:
            if not __jax_installed:
                raise ValueError("You need to install jax to return PRNG key.")
            key = jax.random.PRNGKey(seed_id)
            return key
    else:
        print("Please provide seed_id that isn't None. Using package default.")


def parse_experiment_args(
    default_config_fname: str = "configs/base_config.json",
    default_seed: Union[None, int] = None,
    default_experiment_dir: str = "experiments/",
):
    """Helper function to parse experiment args given to MLExperiment."""
    parser = argparse.ArgumentParser()
    # Standard inputs for training runs (config to load & experiment directory)
    parser.add_argument(
        "-config",
        "--config_fname",
        action="store",
        default=default_config_fname,
        type=str,
        help="Filename from which to load configuration.",
    )
    parser.add_argument(
        "-exp_dir",
        "--experiment_dir",
        action="store",
        default=default_experiment_dir,
        type=str,
        help="Directory to store logs in.",
    )

    # Command line input for the random seed to replicate experiment
    parser.add_argument(
        "-seed",
        "--seed_id",
        action="store",
        default=default_seed,
        type=int,
        help="Seed id on which to train.",
    )

    # Optional: Checkpoint path to potentially reload model
    parser.add_argument(
        "-model_ckpt",
        "--model_ckpt_path",
        action="store",
        default=None,
        help="Model checkpoint path to reload.",
    )

    # Optional: W&B project name & group, name (experiment purpose)
    parser.add_argument(
        "-wb_project",
        "--wb_project",
        action="store",
        default=None,
        help="W&B project name to log to.",
    )

    parser.add_argument(
        "-wb_group",
        "--wb_group",
        action="store",
        default=None,
        help="W&B group name to log to - short purpose of experiment.",
    )

    parser.add_argument(
        "-wb_name",
        "--wb_name",
        action="store",
        default=None,
        help="W&B run name to log to - short purpose of experiment.",
    )

    cmd_args, extra_args = parser.parse_known_args()
    return cmd_args, extra_args


def load_job_config(
    config_fname: str,
    experiment_dir: str,
    seed_id: Union[None, int] = 0,
    model_ckpt: Union[None, str] = None,
    train_config_ext: Union[None, dict] = None,
    log_config_ext: Union[None, dict] = None,
    model_config_ext: Union[None, dict] = None,
    device_config_ext: Union[None, dict] = None,
) -> Tuple[DotMap, DotMap, DotMap, DotMap]:
    """Prepare job config files for experiment run (add seed id, etc.)."""
    # Load .json/.yaml job config + add config fname/experiment dir
    if os.path.exists(config_fname):
        config = load_config(config_fname, return_dotmap=True)
        # Check that train and log config exist!
        assert "train_config" in config.keys(), "Provide train_config key."
        assert "log_config" in config.keys(), "Provide log_config key."
    else:
        config = DotMap(
            {
                "train_config": {},
                "log_config": {
                    "time_to_track": ["num_updates"],
                    "what_to_track": ["loss"],
                },
            }
        )
        print_framed(f"{config_fname} DOESN'T EXIST - USING DEFAULT INSTEAD")
        config_fname = None

    # Check that `time_to_track` and `what_to_track` keys in log_config
    assert (
        "time_to_track" in config.log_config.keys()
    ), "Provide `time_to_track` in log_config."
    assert (
        "what_to_track" in config.log_config.keys()
    ), "Provide `what_to_track` in log_config."
    config.log_config.config_fname = config_fname
    config.log_config.experiment_dir = experiment_dir

    # Subdivide experiment/job config into model, train and log configs
    # Important change in v0.3.0 - Model/Net config not required!
    if "net_config" in config.keys():
        model_config = DotMap(config["net_config"], _dynamic=False)
    elif "model_config" in config.keys():
        model_config = DotMap(config["model_config"], _dynamic=False)
    else:
        model_config = None
    train_config = DotMap(config["train_config"], _dynamic=False)
    log_config = DotMap(config["log_config"], _dynamic=False)

    # Add device config to the standard configurations
    # In experiment setup this will be passed to get_os_env_ready
    if "device_config" in config.keys():
        device_config = DotMap(config["device_config"], _dynamic=False)
    else:
        device_config = None

    # Add device to train on if not already set in the config file
    if "device_name" in train_config.keys():
        device_name = "cpu"
        if __torch_installed:
            if torch.cuda.is_available():
                device_name = "cuda"
        train_config.device_name = device_name

    # Add tensorboard usage to logging config if desired
    if "tboard_fname" not in log_config.keys():
        if "use_tboard" in log_config.keys():
            if log_config.use_tboard:
                tboard_temp = os.path.split(config_fname)[1]
                tboard_base = os.path.splitext(tboard_temp)[0]
                log_config.tboard_fname = tboard_base

    # Set seed for run of your choice - has to be done via command line
    if seed_id is not None:
        train_config.seed_id = int(seed_id)
        log_config.seed_id = seed_id
    else:
        try:
            log_config.seed_id = train_config.seed_id
        except Exception:
            log_config.seed_id = "seed_default"

    # Add model checkpoint string to train configuration
    if model_ckpt is not None:
        train_config.model_ckpt = model_ckpt

    # If train_config_ext, log_config_ext, model_config_ext, device_config_ext
    # manually provided copy over all key, value pairs
    if train_config_ext is not None:
        for k, v in train_config_ext.items():
            train_config[k] = v
    if log_config_ext is not None:
        for k, v in log_config_ext.items():
            log_config[k] = v
    if model_config_ext is not None:
        if model_config is None:
            model_config = DotMap({})
        for k, v in model_config_ext.items():
            model_config[k] = v
    if device_config_ext is not None:
        if device_config is None:
            device_config = DotMap({})
        for k, v in device_config_ext.items():
            device_config[k] = v
    return train_config, model_config, log_config, device_config


def get_extra_cmd_line_input(extra_cmd_args: Union[list, None] = None):
    """Parse additional command line inputs & return them as dotmap."""
    # extra_cmd_args is a sequential list of command line keys & arguments
    if extra_cmd_args is not None:
        # Unpack the command line data into a dotmap dict
        extra_input = {}
        num_extra_args = int(len(extra_cmd_args) / 2)
        counter = 0
        for i in range(num_extra_args):
            cmd_val = extra_cmd_args[counter + 1]
            try:
                cmd_val = float(cmd_val)
            except Exception:
                pass
            extra_input[extra_cmd_args[counter]] = cmd_val
            counter += 2
        return DotMap(extra_input, _dynamic=False)
    else:
        return None


def ask_for_resource_to_run():
    """Ask user if they want to exec on remote resource."""
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    resource = input(time_t + " Where to run? [local/slurm/sge/gcp] ")
    while resource not in ["local", "slurm", "sge", "gcp"]:
        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        resource = input(time_t + " Please repeat: [local/slurm/sge/gcp] ")

    if resource == "local":
        resource_to_run = "local"
    elif resource == "slurm":
        resource_to_run = "slurm-cluster"
    elif resource == "sge":
        resource_to_run = "sge-cluster"
    elif resource == "gcp":
        resource_to_run = "gcp-cloud"
    return resource_to_run


def ask_for_binary_input(question: str, default_answer: str = "N"):
    """Ask user if they want to exec on remote resource."""
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    q_str = f"{time_t} {question} [Y/N]"
    print(q_str, end=" ")
    sys.stdout.flush()
    # Loop over experiments to delete until "N" given or timeout after 60 secs
    answer = default_answer
    while True:
        i, o, e = select.select([sys.stdin], [], [], 60)
        if i:
            answer = sys.stdin.readline().strip()
            if answer in ["y", "n", "Y", "N"]:
                break
            else:
                print("Please repeat your answer. [Y/N]")
        else:
            break
    return answer in ["Y", "y"]


def determine_resource() -> str:
    """Check if cluster (sge/slurm) is available - otherwise local."""
    try:
        sp.check_output(["qstat"])
        return "sge-cluster"
    except Exception:
        pass

    try:
        sp.check_output(["squeue"])
        return "slurm-cluster"
    except Exception:
        return "local"


def setup_proxy_server():
    """Set Gcloud creds & port to tunnel for internet connection."""
    if "credentials_path" in mle_config.gcp.keys():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.expanduser(
            mle_config.gcp.credentials_path
        )
    resource_name = determine_resource()
    if resource_name == "slurm-cluster":
        if mle_config.slurm.info.http_proxy != "":
            os.environ["HTTP_PROXY"] = mle_config.slurm.info.http_proxy
            os.environ["HTTPS_PROXY"] = mle_config.slurm.info.https_proxy
    elif resource_name == "sge-cluster":
        if mle_config.sge.info.http_proxy != "":
            os.environ["HTTP_PROXY"] = mle_config.sge.info.http_proxy
            os.environ["HTTPS_PROXY"] = mle_config.sge.info.https_proxy
