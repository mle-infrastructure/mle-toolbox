import os
from typing import Dict, Union
from ..hyperopt import HyperoptLogger


def run_hyperparameter_search(
    resource_to_run: str,
    meta_job_args: Dict[str, str],
    single_job_args: Dict[str, Union[str, int]],
    param_search_args: Dict[
        str, Dict[str, Union[str, bool, Dict[str, Union[str, bool]]]]
    ],
    message_id: Union[str, None] = None,
) -> None:
    """Run a hyperparameter search experiment."""
    # 1. Setup the hyperlogger for the experiment
    hyperlog_fname = os.path.join(meta_job_args["experiment_dir"], "hyper_log.pkl")
    # If experiment does not use meta_log .hdf5 file system - no metric logging
    if "no_results_logging" not in param_search_args["search_logging"].keys():
        param_search_args["search_logging"]["no_results_logging"] = False
    hyper_log = HyperoptLogger(hyperlog_fname, **param_search_args["search_logging"])

    # 2. Initialize the hyperparameter optimizer class
    search_types = ["random", "grid", "smbo"]
    if param_search_args["search_config"]["search_type"] == "random":
        from ..hyperopt import RandomHyperoptimisation

        hyperopt = RandomHyperoptimisation
    elif param_search_args["search_config"]["search_type"] == "grid":
        from ..hyperopt import GridHyperoptimisation

        hyperopt = GridHyperoptimisation
    elif param_search_args["search_config"]["search_type"] == "smbo":
        from ..hyperopt import SMBOHyperoptimisation

        hyperopt = SMBOHyperoptimisation
    elif param_search_args["search_config"]["search_type"] == "nevergrad":
        from ..hyperopt import NevergradHyperoptimisation

        hyperopt = NevergradHyperoptimisation
        # Add resource budget to nevergrad configuration
        param_search_args["search_config"]["nevergrad_config"][
            "num_workers"
        ] = param_search_args["search_resources"]["num_evals_per_batch"]
        param_search_args["search_config"]["nevergrad_config"]["budget_size"] = (
            param_search_args["search_resources"]["num_evals_per_batch"]
            * param_search_args["search_resources"]["num_search_batches"]
        )
    else:
        raise ValueError(
            "Please provide a valid \
                          hyperparam search type: {}.".format(
                search_types
            )
        )

    # 4. Run the jobs (only remaining jobs if hyper_log was reloaded)
    hyper_opt_instance = hyperopt(
        hyper_log,
        resource_to_run,
        single_job_args,
        meta_job_args["base_train_config"],
        meta_job_args["base_train_fname"],
        meta_job_args["experiment_dir"],
        **param_search_args["search_config"],
        message_id=message_id,
    )

    # Compute remaining jobs/batches for sync/async scheduling of jobs
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
        completed_batches = int(
            hyper_log.iter_id
            / param_search_args["search_resources"]["num_evals_per_batch"]
        )
        param_search_args["search_resources"]["num_search_batches"] -= completed_batches
    hyper_opt_instance.run_search(**param_search_args["search_resources"])
