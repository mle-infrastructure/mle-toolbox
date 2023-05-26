import os
import logging
from typing import Union, List
from mle_scheduler import MLEJob, MLEQueue
from mle_monitor import MLEProtocol
from mle_toolbox import mle_config, check_single_job_args


def spawn_single_job(
    resource_to_run: str,
    job_filename: str,
    config_filename: str,
    job_arguments: Union[None, dict],
    experiment_dir: str,
    debug_mode: bool = False,
):
    """Spawn a single experiment locally/remote."""
    # -1. Check if all required args are given - otw. add default to copy
    job_arguments = check_single_job_args(resource_to_run, job_arguments.copy())

    # 0. Extract extra_cmd_line_input from job_arguments
    if job_arguments is not None:
        if "extra_cmd_line_input" in job_arguments.keys():
            extra_cmd_line_input = job_arguments["extra_cmd_line_input"]
            del job_arguments["extra_cmd_line_input"]
        else:
            extra_cmd_line_input = None

    # 1. Instantiate the experiment class
    experiment = MLEJob(
        resource_to_run=resource_to_run,
        job_filename=job_filename,
        job_arguments=job_arguments,
        config_filename=config_filename,
        experiment_dir=experiment_dir,
        extra_cmd_line_input=extra_cmd_line_input,
        cloud_settings=mle_config.gcp,
        debug_mode=debug_mode,
    )
    # 2. Run the single experiment
    status_out = experiment.run()
    return status_out


def spawn_processing_job(
    resource_to_run: str,
    job_filename: str,
    job_arguments: Union[None, dict],
    experiment_dir: str,
    extra_cmd_line_input: Union[None, dict],
    debug_mode: bool = False,
):
    """
    Spawn a single experiment locally/remote to generate figures, or preprocess
    data, etc.. No .json configuration file required here!
    """
    # 0. Check if all required args are given - otw. add default to copy
    job_arguments = check_single_job_args(resource_to_run, job_arguments.copy())

    # 1. Instantiate the experiment class
    experiment = MLEJob(
        resource_to_run=resource_to_run,
        job_filename=job_filename,
        job_arguments=job_arguments,
        config_filename=None,
        experiment_dir=experiment_dir,
        extra_cmd_line_input=extra_cmd_line_input,
        debug_mode=debug_mode,
        cloud_settings=mle_config.gcp,
    )
    # 2. Run the single pre/post-processing job
    status_out = experiment.run()
    return status_out


def spawn_multiple_seeds(
    resource_to_run: str,
    job_filename: str,
    config_filename: str,
    job_arguments: Union[None, dict],
    experiment_dir: str,
    num_seeds: int,
    default_seed: int = 0,
    random_seeds: Union[None, List[int]] = None,
    logger_level: int = logging.WARNING,
    debug_mode: bool = False,
):
    """Spawn same experiment w. diff. seeds multiple times locally/remote."""
    # 0. Check if all required args are given - otw. add default to copy
    job_arguments = check_single_job_args(resource_to_run, job_arguments.copy())

    # 1. Instantiate the experiment class
    multi_experiment = MLEQueue(
        resource_to_run=resource_to_run,
        job_filename=job_filename,
        job_arguments=job_arguments,
        config_filenames=[config_filename],
        experiment_dir=experiment_dir,
        num_seeds=num_seeds,
        random_seeds=random_seeds,
        max_running_jobs=num_seeds,
        automerge_seeds=True,
        cloud_settings=mle_config.gcp,
        debug_mode=debug_mode,
    )

    # 2. Run the multi-seed job
    multi_experiment.run()


def spawn_multiple_configs(
    resource_to_run: str,
    job_filename: str,
    config_filenames: Union[List[str], str],
    job_arguments: Union[None, dict],
    experiment_dir: str,
    num_seeds: Union[None, int] = None,
    random_seeds: Union[None, List[int]] = None,
    slack_message_id: Union[str, None] = None,
    protocol_db: Union[MLEProtocol, None] = None,
    logger_level: int = logging.WARNING,
    debug_mode: bool = False,
):
    """Spawn processes to running diff. training configs over diff. seeds."""
    # 0. Check if all required args are given - otw. add default to copy
    job_arguments = check_single_job_args(resource_to_run, job_arguments.copy())

    # Check if all config files exist
    for config_fname in config_filenames:
        assert os.path.exists(config_fname)

    if num_seeds is None:
        num_seeds = len(random_seeds)

    # Ensure that config filenames is a list
    if type(config_filenames) is not list:
        config_filenames = [config_filenames]
    num_configs = len(config_filenames)

    # Log the beginning of multiple config experiments
    logger = logging.getLogger(__name__)
    logger.setLevel(logger_level)

    logger.info(
        "START - {} configurations & {} random seeds".format(
            num_configs, num_seeds
        )
    )

    # Run Experiment Jobs in Batch mode!
    default_seed = 0
    multi_experiment = MLEQueue(
        resource_to_run=resource_to_run,
        job_filename=job_filename,
        job_arguments=job_arguments,
        config_filenames=config_filenames,
        experiment_dir=experiment_dir,
        num_seeds=num_seeds,
        default_seed=default_seed,
        random_seeds=random_seeds,
        max_running_jobs=num_seeds * num_configs,
        automerge_configs=True,
        cloud_settings=mle_config.gcp,
        use_slack_bot=mle_config.general.use_slack_bot,
        slack_message_id=slack_message_id,
        slack_user_name=mle_config.slack.user_name,
        slack_auth_token=mle_config.slack.slack_token,
        protocol_db=protocol_db,
        debug_mode=debug_mode,
    )
    multi_experiment.run()

    logger.info(
        "DONE  - different {} configurations & {} random seeds".format(
            num_configs, num_seeds
        )
    )
