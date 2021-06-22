import os
import logging
import time
import datetime
import logging
from typing import Union
import numpy as np
from .experiment import Experiment
from ..utils import merge_hdf5_files


class MultiSeedExperiment(object):
    def __init__(self,
                 resource_to_run: str,
                 job_filename: str,
                 config_filename: Union[None, str],
                 job_arguments: Union[None, dict],
                 experiment_dir: str,
                 num_seeds: int,
                 default_seed: int=0,
                 logger_level: str=logging.WARNING):
        # Init experiment class with relevant info
        self.resource_to_run = resource_to_run     # compute resource for job
        self.job_filename = job_filename           # path to train script
        self.config_filename = config_filename     # path to config json
        self.experiment_dir = experiment_dir       # main results dir (create)
        self.job_arguments = job_arguments         # job-specific args
        self.num_seeds = num_seeds                 # number seeds to run

        # Instantiate/connect a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logger_level)

        # Recreate directory in which the results are stored - later merge
        timestr = datetime.datetime.today().strftime("%Y-%m-%d")[2:] + "_"
        self.base_str = os.path.split(config_filename)[1].split(".")[0]
        self.log_dir = os.path.join(experiment_dir,
                                    timestr + self.base_str + "/logs/")

        # Generate a list of dictionaries with different random seed cmd input
        if self.num_seeds > 1:
            seeds_to_sample = np.arange(100000, 999999)
            random_seeds = np.random.choice(seeds_to_sample, self.num_seeds,
                                            replace=False).tolist()
        else:
            random_seeds = [default_seed]
        self.cmd_line_inputs = [{"seed_id": seed_id} for seed_id
                                in random_seeds]

    def run(self):
        """ Launch -> Monitor -> Merge individual logs. """
        # 1. Launch jobs - one for each random seed
        self.logger.info("START - {} random seeds - {}".format(
                                                        self.num_seeds,
                                                        self.config_filename))
        all_experiments, all_job_ids = self.launch()
        # 2. Monitor jobs until they are completed
        self.monitor(all_experiments, all_job_ids, continuous=True)
        self.logger.info("DONE  - {} random seeds - {}".format(
                                                        self.num_seeds,
                                                        self.config_filename))
        # 3. Merge logs of individual seeds into one collective one
        log_paths, collected_log_path = self.merge_logs()
        self.logger.info("MERGE - {} logs: {}".format(len(log_paths),
                                                      collected_log_path))

    def launch(self):
        """ Launch a set of jobs for one configuration - one for each seed. """
        # 0. Extract extra_cmd_line_input from job_arguments
        if self.job_arguments is not None:
            if "extra_cmd_line_input" in self.job_arguments.keys():
                extra_cmd_line_input = self.job_arguments["extra_cmd_line_input"]
                del self.job_arguments["extra_cmd_line_input"]
            else:
                extra_cmd_line_input = None

        all_experiments, all_job_ids = [], []
        # Loop over individual random seeds to launch
        for cmd_line_input in self.cmd_line_inputs:
            # 1. Instantiate the experiment class and start a single seed
            experiment = Experiment(self.resource_to_run,
                                    self.job_filename,
                                    self.config_filename,
                                    self.job_arguments,
                                    self.experiment_dir,
                                    cmd_line_input,
                                    extra_cmd_line_input)
            # 2. Launch a single experiment
            job_id = experiment.schedule()
            # 3. Collect all job ids and experiment instances
            all_experiments.append(experiment)
            all_job_ids.append(job_id)

        # Return list of `Experiment` instances and their job IDs
        return all_experiments, all_job_ids

    def monitor(self, all_experiments: list, all_job_ids: list,
                continuous: bool=True):
        """ Monitor all seed-specific jobs for one eval configuration. """
        if continuous:
            while True:
                collective_status = 0
                for i, experiment in enumerate(all_experiments):
                    collective_status += experiment.monitor(all_job_ids[i],
                                                            False)
                if collective_status == 0:
                    return 0
        else:
            collective_status = 0
            for i, experiment in enumerate(all_experiments):
                collective_status += experiment.monitor(all_job_ids[i],
                                                        False)
            return collective_status > 0

    def merge_logs(self):
        """ Collect all seed-specific seeds into single <eval_id>.hdf5 file. """
        # Only merge logs if experiment is based on python experiment!
        # Otherwise .hdf5 file system is not used and there is nothing to merge
        filename, file_extension = os.path.splitext(self.job_filename)
        if file_extension == ".py":
            # Merge all resulting .hdf5 files for different seeds into single log
            collected_log_path = os.path.join(self.log_dir,
                                              self.base_str + ".hdf5")
            while True:
                log_paths = [os.path.join(self.log_dir, l)
                             for l in os.listdir(self.log_dir)]
                # print(len(log_paths))
                if len(log_paths) == self.num_seeds:
                    # Delete joined log if at some point over-eagerly merged
                    if collected_log_path in log_paths:
                        os.remove(collected_log_path)
                    break
                else: time.sleep(1)

            merge_hdf5_files(collected_log_path, log_paths,
                             delete_files=True)
            return log_paths, collected_log_path
        else:
            return [], []
