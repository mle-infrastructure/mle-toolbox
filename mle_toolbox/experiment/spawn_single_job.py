from typing import Union
from ..experiment import Experiment


def spawn_single_experiment(job_filename: str,
                            config_filename: str,
                            job_arguments: Union[None, dict],
                            experiment_dir: str,
                            cmd_line_input: Union[None, dict]=None):
    """ Spawn a single experiment locally/remote. """
    # 1. Instantiate the experiment class
    experiment = Experiment(job_filename,
                            config_filename,
                            job_arguments,
                            experiment_dir,
                            cmd_line_input)
    # 2. Run the single experiment
    status_out = experiment.run()
    return status_out


def spawn_post_processing_job(job_filename: str,
                              job_arguments: Union[None, dict],
                              experiment_dir: str,
                              extra_cmd_line_input: Union[None, dict]):
    """ Spawn a single experiment locally/remote to generate figures, etc. """
    # 1. Instantiate the experiment class
    experiment = Experiment(job_filename=job_filename,
                            config_filename=None,
                            job_arguments=job_arguments,
                            experiment_dir=experiment_dir,
                            cmd_line_input={},
                            extra_cmd_line_input=extra_cmd_line_input)
    # 2. Run the single post-processing job
    status_out = experiment.run()
    return status_out
