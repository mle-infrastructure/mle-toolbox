import os
import yaml
import toml
import commentjson
import pickle
from dotmap import DotMap
from typing import Union, Dict, Tuple, Any

# Import helpers for loading meta-log and hyper-log files
from .load_hyper_log import load_hyper_log, HyperLog
from mle_logging import load_meta_log, MetaLog


def load_mle_toolbox_config(config_fname: str = "~/mle_config.toml") -> DotMap:
    """Load cluster config from the .toml file. See docs for more info."""
    # This assumes that the config file is always named the same way!
    try:
        mle_config = DotMap(toml.load(os.path.expanduser(config_fname)), _dynamic=False)
    except Exception:
        print(
            f"Could not load mle-toolbox configuration .toml from {config_fname}"
            "Proceed with minimal config used for testing."
        )
        mle_config = DotMap(
            {
                "general": {
                    "use_conda_virtual_env": False,
                    "use_venv_virtual_env": False,
                    "use_credential_encryption": False,
                    "random_seed": 42,
                    "use_gcloud_protocol_sync": False,
                    "local_protocol_fname": "~/local_mle_protocol.db",
                }
            }
        )

    # Decrypt ssh credentials for SGE & Slurm -> Only if local launch used!
    if mle_config.general.use_credential_encryption:
        # Import decrypt functionality - requires pycrypto!
        try:
            from mle_toolbox.initialize.crypto_credentials import (
                decrypt_ssh_credentials,
            )
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError(
                f"{err}. You need to"
                "install `pycrypto` to use "
                "`decrypt_ssh_credentials`."
            )
        # Decrypt for slurm and sge independently - if key provided!
        assert (
            "aes_key" in mle_config["slurm"].credentials.keys()
            or "aes_key" in mle_config["sge"].credentials.keys()
        ), (
            "If you want to use encrypted credentials, please provide "
            "the aes_key in your mle_config.toml file."
        )
        # TODO: Load aes_key from separate file in encrypted form
        # Assert that the key has the right shape
        for resource in ["slurm", "sge"]:
            if "aes_key" in mle_config[resource].credentials.keys():
                dec_user, dec_pass = decrypt_ssh_credentials(
                    mle_config[resource].credentials.aes_key,
                    mle_config[resource].credentials.user_name,
                    mle_config[resource].credentials.password,
                )
                mle_config[resource].credentials.user_name = dec_user
                mle_config[resource].credentials.password = dec_pass

    return mle_config


def load_yaml_config(cmd_args: dict) -> DotMap:
    """Load in YAML config file, overwrite based on cmd & wrap as DotMap."""
    with open(cmd_args.config_fname) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

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
    ), "Job type has to be in {all_experiment_types}."

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
    assert os.path.isfile(config["meta_job_args"]["base_train_fname"])
    assert os.path.isfile(config["meta_job_args"]["base_train_config"])
    return DotMap(config, _dynamic=False)


def load_json_config(config_fname: str) -> Dict[str, Union[str, int, dict]]:
    """Load in a config JSON file and return as a dictionary"""
    json_config = commentjson.loads(open(config_fname, "r").read())
    dict_config = DotMap(json_config, _dynamic=False)

    # Check that train_config/log_config are provided.
    # Note that model_config is left optional.
    assert "train_config" in dict_config.keys(), "Provide train_config key."
    assert "log_config" in dict_config.keys(), "Provide log_config key."
    return dict_config


def load_pkl_object(filename: str) -> Any:
    """Helper to reload pickle objects."""
    with open(filename, "rb") as input:
        obj = pickle.load(input)
    return obj


def load_result_logs(
    experiment_dir: str = "experiments",
    meta_log_fname: str = "meta_log.hdf5",
    hyper_log_fname: str = "hyper_log.pkl",
) -> Tuple[MetaLog, HyperLog]:
    """Load both meta and hyper logs for an experiment."""
    meta_log = load_meta_log(os.path.join(experiment_dir, meta_log_fname))
    hyper_log = load_hyper_log(os.path.join(experiment_dir, hyper_log_fname))
    # Reconstruct search variables and evaluation metrics
    hyper_log.set_search_metrics(
        meta_log.meta_vars, meta_log.stats_vars, meta_log.time_vars
    )
    return meta_log, hyper_log
