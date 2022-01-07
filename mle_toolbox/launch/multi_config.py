import logging
from typing import Union
from .spawn_jobs import spawn_multiple_configs
from mle_monitor import MLEProtocol


def run_multiple_configs(
    resource_to_run: str,
    meta_job_args: dict,
    single_job_args: dict,
    multi_config_args: dict,
    message_id: Union[str, None] = None,
    protocol_db: Union[MLEProtocol, None] = None,
    debug_mode: bool = False,
):
    """Run an experiment over different configurations (+random seeds)."""
    if "num_seeds" not in multi_config_args.keys():
        multi_config_args["num_seeds"] = len(multi_config_args["random_seeds"])
    if "random_seeds" not in multi_config_args.keys():
        multi_config_args["random_seeds"] = None

    # 1. Create multiple experiment instances and submit the jobs
    spawn_multiple_configs(
        resource_to_run,
        meta_job_args["base_train_fname"],
        multi_config_args["config_fnames"],
        single_job_args,
        meta_job_args["experiment_dir"],
        num_seeds=multi_config_args["num_seeds"],
        random_seeds=multi_config_args["random_seeds"],
        slack_message_id=message_id,
        protocol_db=protocol_db,
        logger_level=logging.INFO,
        debug_mode=debug_mode,
    )
