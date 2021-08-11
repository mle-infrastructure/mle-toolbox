import logging
from typing import Union
from ..job import spawn_multiple_configs


def run_multiple_configs(
    resource_to_run: str,
    meta_job_args: dict,
    single_job_args: dict,
    multi_config_args: dict,
    message_id: Union[str, None] = None,
):
    """Run an experiment over different configurations (+random seeds)."""
    # 1. Create multiple experiment instances and submit the jobs
    spawn_multiple_configs(
        resource_to_run,
        meta_job_args["base_train_fname"],
        multi_config_args["config_fnames"],
        single_job_args,
        meta_job_args["experiment_dir"],
        num_seeds=multi_config_args["num_seeds"],
        random_seeds=multi_config_args["random_seeds"],
        message_id=message_id,
        logger_level=logging.INFO,
    )
