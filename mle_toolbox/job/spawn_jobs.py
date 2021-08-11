import logging
from typing import Union, List
from .job import Job
from .job_queue import JobQueue


def spawn_single_job(
    resource_to_run: str,
    job_filename: str,
    config_filename: str,
    job_arguments: Union[None, dict],
    experiment_dir: str,
    cmd_line_input: Union[None, dict] = None,
):
    """Spawn a single experiment locally/remote."""
    # 0. Extract extra_cmd_line_input from job_arguments
    if job_arguments is not None:
        if "extra_cmd_line_input" in job_arguments.keys():
            extra_cmd_line_input = job_arguments["extra_cmd_line_input"]
            del job_arguments["extra_cmd_line_input"]
        else:
            extra_cmd_line_input = None

    # 1. Instantiate the experiment class
    experiment = Job(
        resource_to_run,
        job_filename,
        config_filename,
        job_arguments,
        experiment_dir,
        cmd_line_input,
        extra_cmd_line_input,
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
):
    """
    Spawn a single experiment locally/remote to generate figures, or preprocess
    data, etc.. No .json configuration file required here!
    """
    # 1. Instantiate the experiment class
    experiment = Job(
        resource_to_run=resource_to_run,
        job_filename=job_filename,
        config_filename=None,
        job_arguments=job_arguments,
        experiment_dir=experiment_dir,
        cmd_line_input={},
        extra_cmd_line_input=extra_cmd_line_input,
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
):
    """Spawn same experiment w. diff. seeds multiple times locally/remote."""
    multi_experiment = JobQueue(
        resource_to_run,
        job_filename,
        [config_filename],
        job_arguments,
        experiment_dir,
        num_seeds,
        random_seeds=random_seeds,
        max_running_jobs=num_seeds,
    )
    multi_experiment.run()


def spawn_multiple_configs(
    resource_to_run: str,
    job_filename: str,
    config_filenames: Union[List[str], str],
    job_arguments: Union[None, dict],
    experiment_dir: str,
    num_seeds: Union[None, int] = None,
    random_seeds: Union[None, List[int]] = None,
    message_id: Union[str, None] = None,
    logger_level: int = logging.WARNING,
):
    """Spawn processes to running diff. training configs over diff. seeds."""
    if num_seeds is None:
        num_seeds = 1

    # Ensure that config filenames is a list
    if type(config_filenames) is not list:
        config_filenames = [config_filenames]
    num_configs = len(config_filenames)

    # Log the beginning of multiple config experiments
    logger = logging.getLogger(__name__)
    logger.setLevel(logger_level)

    logger.info(
        "START - {} configurations " "& {} random seeds".format(num_configs, num_seeds)
    )

    # Run Experiment Jobs in Batch mode!
    default_seed = 0
    multi_experiment = JobQueue(
        resource_to_run,
        job_filename,
        config_filenames,
        job_arguments,
        experiment_dir,
        num_seeds,
        default_seed,
        random_seeds,
        num_seeds * num_configs,
        message_id,
    )
    multi_experiment.run()

    logger.info(
        "DONE  - different {} configurations "
        "& {} random seeds".format(num_configs, num_seeds)
    )
