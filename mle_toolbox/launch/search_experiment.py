import os
from typing import Dict, Union
from ..hyperopt import HyperoptLogger, MLE_BatchSearch
from pathlib import Path
from mle_monitor import MLEProtocol


def run_hyperparameter_search(
    resource_to_run: str,
    meta_job_args: Dict[str, str],
    single_job_args: Dict[str, Union[str, int]],
    param_search_args: Dict[
        str, Dict[str, Union[str, bool, Dict[str, Union[str, bool]]]]
    ],
    message_id: Union[str, None] = None,
    protocol_db: Union[MLEProtocol, None] = None,
) -> None:
    """Run a hyperparameter search experiment for multiple configurations."""
    if type(meta_job_args["base_train_config"]) == list:
        experiment_dirs, config_files = [], []
        for config in meta_job_args["base_train_config"]:
            experiment_dirs.append(
                os.path.join(meta_job_args["experiment_dir"], Path(config).stem)
            )
            config_files.append(config)
    else:
        config_files = [meta_job_args["base_train_config"]]
        experiment_dirs = [meta_job_args["experiment_dir"]]

    if meta_job_args["experiment_type"] == "hyperparameter-search":
        for i in range(len(config_files)):
            run_single_batch_search(
                resource_to_run,
                meta_job_args["base_train_fname"],
                config_files[i],
                experiment_dirs[i],
                single_job_args,
                param_search_args,
                message_id,
                protocol_db,
            )


def run_single_batch_search(
    resource_to_run: str,
    train_fname: str,
    train_config: str,
    experiment_dir: str,
    single_job_args: Dict[str, Union[str, int]],
    param_search_args: Dict[
        str, Dict[str, Union[str, bool, Dict[str, Union[str, bool]]]]
    ],
    message_id: Union[str, None] = None,
    protocol_db: Union[MLEProtocol, None] = None,
) -> None:
    """Run a hyperparameter search experiment for a single configuration."""
    # 1. Setup the hyperlogger for the experiment
    hyperlog_fname = os.path.join(experiment_dir, "hyper_log.pkl")
    # If experiment does not use meta_log .hdf5 file system - no metric logging
    if "no_results_logging" not in param_search_args["search_logging"].keys():
        param_search_args["search_logging"]["no_results_logging"] = False
    hyper_log = HyperoptLogger(hyperlog_fname, **param_search_args["search_logging"])

    # 2. Initialize the hyperparameter optimizer class
    search_types = [
        "Random",
        "Grid",
        "SMBO",
        "Nevergrad",
        "Coordinate",
        "Halving",
        "Hyperband",
        "PBT",
    ]
    assert param_search_args["search_config"]["search_type"] in search_types

    # Add budgets to config (special cases: Nevergrad, PBT, Halving, Hyperband)
    if param_search_args["search_config"]["search_type"] == "Nevergrad":
        param_search_args["search_config"]["search_config"][
            "num_workers"
        ] = param_search_args["search_resources"]["num_evals_per_batch"]
        param_search_args["search_config"]["search_config"]["budget_size"] = (
            param_search_args["search_resources"]["num_evals_per_batch"]
            * param_search_args["search_resources"]["num_search_batches"]
        )

    elif param_search_args["search_config"]["search_type"] == "PBT":
        param_search_args["search_config"]["search_resources"][
            "num_evals_per_batch"
        ] = param_search_args["search_config"]["search_config"]["num_workers"]

    # 4. Compute remaining jobs/batches for sync/async scheduling of jobs
    if "search_schedule" in param_search_args["search_config"].keys():
        if param_search_args["search_config"]["search_schedule"] == "async":
            param_search_args["search_resources"][
                "num_total_evals"
            ] -= hyper_log.iter_id
        elif param_search_args["search_config"]["search_schedule"] == "sync":
            completed_batches = int(
                hyper_log.iter_id
                / param_search_args["search_resources"]["num_evals_per_batch"]
            )
            param_search_args["search_resources"][
                "num_search_batches"
            ] -= completed_batches
    else:
        # Default to batch case - if no search_schedule provided!
        completed_batches = int(
            hyper_log.iter_id
            / param_search_args["search_resources"]["num_evals_per_batch"]
        )
        param_search_args["search_resources"]["num_search_batches"] -= completed_batches

    # 5. Run the jobs (only remaining jobs if reloaded)
    hyper_opt_instance = MLE_BatchSearch(
        hyper_log,
        resource_to_run,
        single_job_args,
        train_config,
        train_fname,
        experiment_dir,
        **param_search_args["search_config"],
        message_id=message_id,
        protocol_db=protocol_db
    )

    hyper_opt_instance.run_search(**param_search_args["search_resources"])
