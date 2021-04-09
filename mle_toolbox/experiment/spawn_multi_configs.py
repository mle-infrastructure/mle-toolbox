import os
import logging
import datetime
import time
from typing import List, Union
import multiprocessing as mp
from .spawn_multi_seed import spawn_multiple_seeds_experiment


def spawn_multiple_configs(job_filename: str,
                           config_filenames: Union[List[str], str],
                           job_arguments: Union[None, dict],
                           experiment_dir: str,
                           num_seeds: Union[None, int] = None,
                           logger_level: int=logging.WARNING):
    """ Spawn processes to running diff. training configs over diff. seeds. """
    num_configs = len(config_filenames)
    if num_seeds is None:
        num_seeds = 1
    spawn_multiple_configs_experiment(job_filename, config_filenames,
                                      job_arguments, experiment_dir,
                                      num_seeds, logger_level)
    return 1


def spawn_multiple_configs_experiment(job_filename: str,
                                      config_filenames: Union[List[str], str],
                                      job_arguments: Union[None, dict],
                                      experiment_dir: str,
                                      num_seeds: Union[None, int] = None,
                                      logger_level: int=logging.WARNING):
    """ Spawn multi experiments w. diff. configs/seeds locally/remote. """
    # Ensure that config filenames is a list
    if type(config_filenames) is not list:
        config_filenames = [config_filenames]
    num_configs = len(config_filenames)

    # Log the beginning of multiple config experiments
    logger = logging.getLogger(__name__)
    logger.setLevel(logger_level)

    logger.info("START - {} configurations " \
                "& {} random seeds".format(num_configs, num_seeds))

    # Spawn the different processes for the different seeds
    if num_seeds is not None:
        procs = [mp.Process(target=spawn_multiple_seeds_experiment,
                            args=(job_filename,
                                  config_filenames[i],
                                  job_arguments,
                                  experiment_dir,
                                  num_seeds)) for i in range(num_configs)]

        # Wait a milli-second before submitting the next job
        for p in procs:
            p.start()
            time.sleep(0.1)
        [p.join() for p in procs]
        logger.info("DONE  - different {} configurations " \
                    "& {} random seeds".format(num_configs, num_seeds))

    # Need some valid input!
    else:
        raise ValueError("Please provide a number of seeds to " \
                         "your training/simulation over.")
