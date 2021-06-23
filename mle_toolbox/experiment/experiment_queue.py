import os
import logging
import time
import datetime
from tqdm import tqdm

import logging
from typing import Union
import numpy as np
from .experiment import Experiment
from ..utils import merge_hdf5_files


class ExperimentQueue(object):
    """
    Multi-Seed Experiment Class: This is essentially a for-loop handler for
    the `Experiment` class when running multiple random seeds.
    """
    def __init__(self,
                 resource_to_run: str,
                 job_filename: str,
                 config_filenames: Union[None, str],
                 job_arguments: Union[None, dict],
                 experiment_dir: str,
                 num_seeds: int,
                 default_seed: int=0,
                 max_running_jobs: int=10,
                 logger_level: int=logging.WARNING):
        # Init experiment class with relevant info
        self.resource_to_run = resource_to_run     # compute resource for job
        self.job_filename = job_filename           # path to train script
        self.config_filenames = config_filenames   # path to config json
        self.experiment_dir = experiment_dir       # main results dir (create)
        self.job_arguments = job_arguments         # job-specific args
        self.num_seeds = num_seeds                 # number seeds to run
        self.max_running_jobs = max_running_jobs   # number of sim running jobs

        # Instantiate/connect a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logger_level)

        # Generate a list of dictionaries with different random seed cmd input
        if self.num_seeds > 1:
            seeds_to_sample = np.arange(100000, 999999)
            self.random_seeds = np.random.choice(seeds_to_sample,
                                                 self.num_seeds,
                                                 replace=False).tolist()
        else:
            self.random_seeds = [default_seed]

        # Extract extra_cmd_line_input from job_arguments
        if self.job_arguments is not None:
            if "extra_cmd_line_input" in self.job_arguments.keys():
                self.extra_cmd_line_input = self.job_arguments["extra_cmd_line_input"]
                del self.job_arguments["extra_cmd_line_input"]
            else:
                self.extra_cmd_line_input = None

        # Generate a list of jobs to be queued/executed on the resource
        # Recreate directory in which the results are stored - later merge
        # 3 status types: -1 - not started yet; 0 - completed, 1 - running
        timestr = datetime.datetime.today().strftime("%Y-%m-%d")[2:] + "_"
        self.queue = []
        for config_fname in self.config_filenames:
            base_str = os.path.split(config_fname)[1].split(".")[0]
            for seed_id in self.random_seeds:
                self.queue.append(
                    {'config_fname': config_fname,
                     'seed_id': seed_id,
                     'base_str': base_str,
                     'log_dir': os.path.join(experiment_dir,
                                             timestr + base_str + "/logs/"),
                     'status': -1,
                     'experiment': None,
                     'job_id': None,
                     'merged_logs': False})

        self.queue_counter = 0        # Next job to schedule
        self.num_completed_jobs = 0   # No. already completed experiments
        self.num_running_jobs = 0     # No. of currently running jobs
        self.num_total_jobs = len(self.queue)

        self.logger.info("QUEUED - {} random seeds - {} configs".format(
                                                    self.num_seeds,
                                                    len(self.config_filenames)))
        self.logger.info("TOTAL JOBS TO EXECUTE - {}".format(self.num_total_jobs))

    def run(self):
        """ Launch -> Monitor -> Merge individual logs. """
        # 1. Spawn 1st batch of evals until limit of allowed usage is reached
        while self.num_running_jobs < min(self.max_running_jobs,
                                          self.num_total_jobs):
            experiment, job_id = self.launch(self.queue_counter)
            self.queue[self.queue_counter]["status"] = 1
            self.queue[self.queue_counter]["experiment"] = experiment
            self.queue[self.queue_counter]["job_id"] = job_id
            self.num_running_jobs += 1
            self.queue_counter += 1
            time.sleep(0.1)
        self.logger.info("LAUNCH - FIRST {}/{} SET OF JOBS".format(
                                                        self.num_running_jobs,
                                                        self.num_total_jobs))

        # 2. Set up Progress Bar Counter of completed jobs
        self.pbar = tqdm(total=self.num_total_jobs,
                         bar_format='{l_bar}{bar:45}{r_bar}{bar:-45b}')

        # 3. Monitor & launch new waiting jobs when resource available
        while self.num_completed_jobs < self.num_total_jobs:
            # Once budget is fully allocated - start monitor running jobs
            # Loop over all jobs in queue - check status of prev running
            for job in self.queue:
                if job["status"] == 1:
                    status = self.monitor(job["experiment"], job["job_id"],
                                          False)
                    # If status changes to completed - update counters/state
                    if status == 0:
                        self.num_completed_jobs += 1
                        self.num_running_jobs -= 1
                        job["status"] = 0
                        self.pbar.update(1)

                        # Merge seeds of one eval/config if all jobs done!
                        completed_seeds = 0
                        for other_job in self.queue:
                            if other_job["config_fname"] == job["config_fname"]:
                                if other_job["status"] == 0:
                                    completed_seeds += 1
                        if completed_seeds == self.num_seeds:
                            self.merge_logs(job["log_dir"], job["base_str"])
                time.sleep(0.1)

            # Once budget becomes available again - fill up with new jobs
            while self.num_running_jobs < min(self.max_running_jobs,
                                              self.num_total_jobs
                                              - self.num_completed_jobs
                                              - self.num_running_jobs):
                experiment, job_id = self.launch(self.queue_counter)
                self.queue[self.queue_counter]["status"] = 1
                self.queue[self.queue_counter]["experiment"] = experiment
                self.queue[self.queue_counter]["job_id"] = job_id
                self.num_running_jobs += 1
                self.queue_counter += 1
                time.sleep(0.1)
        self.pbar.close()

    def launch(self, queue_counter):
        """ Launch a set of jobs for one configuration - one for each seed. """
        # 1. Instantiate the experiment class and start a single seed
        cmd_line_input = {"seed_id": self.queue[queue_counter]["seed_id"]}
        experiment = Experiment(self.resource_to_run,
                                self.job_filename,
                                self.queue[queue_counter]["config_fname"],
                                self.job_arguments,
                                self.experiment_dir,
                                cmd_line_input,
                                self.extra_cmd_line_input)

        # 2. Launch a single experiment
        job_id = experiment.schedule()

        # 3. Return updated counter, `Experiment` instance & corresponding ID
        return experiment, job_id

    def monitor(self, experiment: Experiment, job_id: str,
                continuous: bool=True):
        """ Monitor all seed-specific jobs for one eval configuration. """
        if continuous:
            while True:
                status = experiment.monitor(all_job_ids[i], False)
                if status == 0:
                    return 0
        else:
            status = experiment.monitor(job_id, False)
            return status

    def merge_logs(self, log_dir: str, base_str: str):
        """ Collect all seed-specific seeds into single <eval_id>.hdf5 file. """
        # Only merge logs if experiment is based on python experiment!
        # Otherwise .hdf5 file system is not used and there is nothing to merge
        filename, file_extension = os.path.splitext(self.job_filename)
        if file_extension == ".py":
            # Merge all resulting .hdf5 files for different seeds into single log
            collected_log_path = os.path.join(log_dir, base_str + ".hdf5")
            while True:
                log_paths = [os.path.join(log_dir, l)
                             for l in os.listdir(log_dir)]
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
