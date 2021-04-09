import os
import logging
import time
import datetime
from typing import Union
import numpy as np
import multiprocessing as mp

from .spawn_single_job import spawn_single_experiment
from ..utils.manipulate_files import merge_hdf5_files


def spawn_multiple_seeds_experiment(job_filename: str,
                                    config_filename: str,
                                    job_arguments: Union[None, dict],
                                    experiment_dir: str,
                                    num_seeds: int,
                                    default_seed: int=0,
                                    logger_level: int=logging.WARNING):
    """ Spawn same experiment w. diff. seeds multiple times locally/remote. """
    # Recreate the directory in which the results are stored - later merge
    timestr = datetime.datetime.today().strftime("%Y-%m-%d")[2:] + "_"
    base_str = os.path.split(config_filename)[1].split(".")[0]
    log_dir = os.path.join(experiment_dir, timestr + base_str + "/logs/")

    # Generate a list of dictionaries with different random seed cmd input
    if num_seeds > 1:
        random_seeds = np.random.choice(1000000, num_seeds,
                                        replace=False).tolist()
    else:
        random_seeds = [default_seed]
    cmd_line_inputs = [{"seed_id": seed_id} for seed_id in random_seeds]

    # Log the beginning of multiple seeds experiments
    logger = logging.getLogger(__name__)
    logger.setLevel(logger_level)

    logger.info("START - {} random seeds - {}".format(num_seeds,
                                                      config_filename))

    # Spawn the different processes for the different seeds
    procs = [mp.Process(target=spawn_single_experiment,
                        args=(job_filename,
                              config_filename,
                              job_arguments,
                              experiment_dir,
                              cmd_line_inputs[i])) for i in range(num_seeds)]
    [p.start() for p in procs]
    [p.join() for p in procs]

    logger.info("DONE  - {} random seeds - {}".format(num_seeds,
                                                      config_filename))

    # Merge all resulting .hdf5 files for different seeds into single log
    collected_log_path = os.path.join(log_dir, base_str + ".hdf5")
    while True:
        log_paths = [os.path.join(log_dir, l) for l in os.listdir(log_dir)]
        # print(len(log_paths))
        if len(log_paths) == num_seeds:
            # Delete joined log if at some point over-eagerly merged
            if collected_log_path in log_paths:
                os.remove(collected_log_path)
            break
        else: time.sleep(1)

    merge_hdf5_files(collected_log_path, log_paths, delete_files=True)

    logger.info("MERGE - {} logs: {}".format(len(log_paths),
                                             collected_log_path))
