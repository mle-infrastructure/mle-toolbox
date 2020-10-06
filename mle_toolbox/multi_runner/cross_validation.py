import os
import logging
import time
import datetime
from typing import Union
import numpy as np
import multiprocessing as mp

from .spawn_single_run import spawn_single_experiment
from ..utils import merge_hdf5_files


# Setup the logging style
logging.basicConfig(format='%(asctime)s %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p',
                    level=logging.DEBUG)


def get_crossval_fold_ids(num_data_points: int,
                          num_folds: int) -> np.ndarray:
    """ Generate fold ids for datapoints in diffferent folds. """
    points_per_fold = np.ceil(num_data_points/num_folds)
    fold_ids = np.repeat(np.arange(num_folds),
                         points_per_fold)[:num_data_points]
    np.random.shuffle(fold_ids)
    return fold_ids


def spawn_multiple_folds_experiment(job_filename: str,
                                    config_filename: str,
                                    job_arguments: Union[None, dict],
                                    experiment_dir: str,
                                    fold_args: dict):
    """ Spawn jobs (e.g. over different folds) for a single config. """
    # Recreate the directory in which the results are stored - later merge
    timestr = datetime.datetime.today().strftime("%Y-%m-%d")[2:] + "_"
    base_str = os.path.split(config_filename)[1].split(".")[0]
    base_exp_dir = os.path.join(experiment_dir, timestr + base_str)
    log_dir = os.path.join(base_exp_dir, "logs/")

    # Create a new empty directory for the experiment
    if not os.path.exists(base_exp_dir):
        os.makedirs(base_exp_dir)

    # Construct folds ids to run over (need total amount of samples to split)
    # Allocate datapoint ids to different folds -> store in .npy file
    fold_path = os.path.join(base_exp_dir, fold_args["fold_path"])
    fold_ids = get_crossval_fold_ids(fold_args["num_data_points"],
                                     fold_args["num_folds"])
    np.save(fold_path, fold_ids)

    # Generate a list of dictionaries with different random seed cmd input
    all_fold_ids = np.arange(fold_args["num_folds"])
    cmd_line_inputs = [{"fold_id": fold_id,
                        "fold_path": fold_path}
                       for fold_id in all_fold_ids]

    # Log the beginning of multiple seeds experiments
    logger = logging.getLogger(__name__)
    logger.info("START - {} data folds - {}".format(fold_args["num_folds"],
                                                    config_filename))

    # Spawn the different processes for the different seeds
    procs = [mp.Process(target=spawn_single_experiment,
                        args=(job_filename,
                              config_filename,
                              job_arguments,
                              experiment_dir,
                              cmd_line_inputs[i]))
             for i in range(fold_args["num_folds"])]
    [p.start() for p in procs]
    [p.join() for p in procs]
    logger.info("DONE  - {} data folds - {}".format(fold_args["num_folds"],
                                                    config_filename))

    # Merge all resulting .hdf5 files for different seeds into single log
    collected_log_path = os.path.join(log_dir, base_str + ".hdf5")
    while True:
        log_paths = [os.path.join(log_dir, l) for l in os.listdir(log_dir)]
        if len(log_paths) == fold_args["num_folds"]:
            # print(log_paths)
            # Delete joined log if at some point over-eagerly merged
            if collected_log_path in log_paths:
                os.remove(collected_log_path)
            break
        else: time.sleep(1)

    merge_hdf5_files(collected_log_path, log_paths, delete_files=False)
    logger.info("MERGE - {} logs: {}".format(len(log_paths),
                                             collected_log_path))
