import os
import toml
import pickle
from dotmap import DotMap
from typing import Tuple, Any, List, Union

# Import helpers for loading meta-log and hyper-log files
from .hyper_log import load_hyper_log
from mle_logging import load_log


def load_mle_toolbox_config(config_fname: str = "~/mle_config.toml") -> DotMap:
    """Load cluster config from the .toml file. See docs for more info."""
    # This assumes that the config file is always named the same way!
    try:
        mle_config = DotMap(toml.load(os.path.expanduser(config_fname)), _dynamic=False)
    except Exception:
        print(
            f"Could not load mle-toolbox configuration .toml from {config_fname} \n"
            "Proceed with minimal config used for testing."
        )
        mle_config = DotMap(
            {
                "general": {
                    "use_conda_virtual_env": False,
                    "use_venv_virtual_env": False,
                    "use_slack_bot": False,
                    "random_seed": 42,
                    "local_protocol_fname": "~/local_mle_protocol.db",
                },
                "slack": {
                    "slack_user_name": None,
                    "slack_token": None,
                },
            }
        )
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
    aggregate_seeds: bool = True,
):
    """Load both meta and hyper logs for an experiment."""
    meta_log = load_log(os.path.join(experiment_dir, meta_log_fname), aggregate_seeds)
    hyper_log = load_hyper_log(os.path.join(experiment_dir, hyper_log_fname))
    # Reconstruct search variables and evaluation metrics
    hyper_log.set_search_metrics(
        meta_log.meta_vars, meta_log.stats_vars, meta_log.time_vars
    )
    return meta_log, hyper_log


def combine_experiments(
    experiment_dirs: List[str] = ["experiments"],
    experiment_ids: Union[None, List[str]] = None,
    aggregate_seeds: bool = True,
) -> Tuple[DotMap, DotMap]:
    """Load and combine multiple experiment logs (meta & hyper)."""
    combined_meta, combined_hyper = {}, {}

    # Check if enough experiment_ids are given
    if experiment_ids is not None:
        assert len(experiment_ids) == len(experiment_ids)

    # Loop over individual experiment directories and load results
    for i, e_dir in enumerate(experiment_dirs):
        # Get experiment id from provided list of str or from experiment dir path
        if experiment_ids is not None:
            e_id = experiment_ids[i]
        else:
            e_path = os.path.normpath(e_dir)
            e_id = e_path.split(os.sep)[-1]
        meta, hyper = load_result_logs(e_dir, aggregate_seeds=aggregate_seeds)
        combined_meta[e_id] = meta
        combined_hyper[e_id] = hyper
    return DotMap(combined_meta, _dynamic=False), DotMap(combined_hyper, _dynamic=False)
