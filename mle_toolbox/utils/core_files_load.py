import os
import yaml
import toml
import commentjson
import pickle
from typing import Union, List
from dotmap import DotMap
# Import helpers for loading meta-log and hyper-log files
from .load_meta_log import load_meta_log
from .load_hyper_log import load_hyper_log


def load_mle_toolbox_config():
    """ Load cluster config from the .toml file. See docs for more info. """
    # This assumes that the config file is always named the same way!
    try:
        mle_config = DotMap(toml.load(os.path.expanduser("~/mle_config.toml")),
                                      _dynamic=False)
    except:
        return None

    # Decrypt ssh credentials for SGE & Slurm -> Only if local launch used!
    if mle_config.general.use_credential_encryption:
        # Import decrypt functionality - requires pycrypto!
        try:
            from mle_toolbox.initialize.crypto_credentials import decrypt_ssh_credentials
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError(f"{err}. You need to"
                                      "install `pycrypto` to use "
                                      "`decrypt_ssh_credentials`.")
        # Decrypt for slurm and sge independently - if key provided!
        for resource in ["slurm", "sge"]:
            if "aes_key" in mle_config[resource].credentials.keys():
                dec_user, dec_pass = decrypt_ssh_credentials(
                                mle_config[resource].credentials.aes_key,
                                mle_config[resource].credentials.user_name,
                                mle_config[resource].credentials.password)
                mle_config[resource].credentials.user_name = dec_user
                mle_config[resource].credentials.password = dec_pass
        return mle_config



def load_yaml_config(cmd_args: dict) -> DotMap:
    """ Load in YAML config file, overwrite based on cmd & wrap as DotMap. """
    with open(cmd_args.config_fname) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # Update job config with specific cmd args (if provided)
    if cmd_args.base_train_fname is not None:
        config["meta_job_args"]["base_train_fname"] = cmd_args.base_train_fname
    if cmd_args.base_train_config is not None:
        config["meta_job_args"]["base_train_config"] = cmd_args.base_train_config
    if cmd_args.experiment_dir is not None:
        config["meta_job_args"]["experiment_dir"] = cmd_args.experiment_dir
    return DotMap(config, _dynamic=False)


def load_json_config(config_fname: str) -> DotMap:
    """ Load in a config JSON file and return as a dictionary """
    json_config = commentjson.loads(open(config_fname, 'r').read())
    dict_config = DotMap(json_config, _dynamic=False)
    return dict_config


def load_pkl_object(filename: str):
    """ Helper to reload pickle objects. """
    with open(filename, 'rb') as input:
        obj = pickle.load(input)
    return obj


def load_result_logs(experiment_dir: str,
                     meta_log_fname: str="meta_log.hdf5",
                     hyper_log_fname: str="hyper_log.pkl"):
    """ Load both meta and hyper logs for an experiment. """
    meta_log = load_meta_log(os.path.join(experiment_dir, meta_log_fname))
    hyper_log = load_hyper_log(os.path.join(experiment_dir, hyper_log_fname))
    # Reconstruct search variables and evaluation metrics
    hyper_log.set_search_metrics(meta_log.meta_vars,
                                 meta_log.stats_vars,
                                 meta_log.time_vars)
    return meta_log, hyper_log


def load_run_log(experiment_dir: str, mean_seeds: bool=False):
    """ Load a single .hdf5 log from <experiment_dir>/logs. """
    log_dir = os.path.join(experiment_dir, "logs/")
    log_paths = []
    for file in os.listdir(log_dir):
        if file.endswith(".hdf5"):
            log_paths.append(os.path.join(log_dir, file))
    if len(log_paths) > 1:
        print(f"Multiple .hdf5 files available: {log_paths}")
        print(f"Continue using: {log_paths[0]}")
    run_log = load_meta_log(log_paths[0], mean_seeds)
    return run_log
