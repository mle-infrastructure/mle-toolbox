import os
from typing import Dict, Union


def run_population_based_training(
    resource_to_run: str,
    meta_job_args: Dict[str, str],
    single_job_args: Dict[str, str],
    pbt_args: Dict[str, Union[str, Dict[str, Union[str, int]]]],
) -> None:
    """Run a PBT experiment."""
    from ..pbt import PBT_Logger, PBT_Manager

    # 1. Setup the hyperlogger for the experiment
    pbt_log_fname = os.path.join(meta_job_args["experiment_dir"], "pbt_log.pkl")
    pbt_log = PBT_Logger(
        pbt_log_fname,
        meta_job_args["experiment_dir"],
        pbt_args["pbt_logging"]["eval_metric"],
        pbt_args["pbt_logging"]["max_objective"],
        pbt_args["pbt_resources"]["num_population_members"],
    )

    # 2. Initialize and run the PBT optimizer class
    pbt_opt_instance = PBT_Manager(
        pbt_log,
        resource_to_run,
        single_job_args,
        meta_job_args["base_train_config"],
        meta_job_args["base_train_fname"],
        meta_job_args["experiment_dir"],
        pbt_args["pbt_logging"],
        pbt_args["pbt_resources"],
        pbt_args["pbt_config"],
    )
    pbt_opt_instance.run()
    return
