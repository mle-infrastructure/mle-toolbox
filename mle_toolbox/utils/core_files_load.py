import os
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


def load_pkl_object(filename: str) -> Any:
    """Helper to reload pickle objects."""
    with open(filename, "rb") as input:
        obj = pickle.load(input)
    return obj


def load_result_logs(
    experiment_dir: str = "experiments",
    meta_log_fname: str = "meta_log.hdf5",
    hyper_log_fname: str = "hyper_log.pkl",
    aggregate_seeds: bool = True
) -> Tuple[MetaLog, HyperLog]:
    """Load both meta and hyper logs for an experiment."""
    meta_log = load_meta_log(os.path.join(experiment_dir, meta_log_fname),
                             aggregate_seeds)
    hyper_log = load_hyper_log(os.path.join(experiment_dir, hyper_log_fname))
    # Reconstruct search variables and evaluation metrics
    hyper_log.set_search_metrics(
        meta_log.meta_vars, meta_log.stats_vars, meta_log.time_vars
    )
    return meta_log, hyper_log
