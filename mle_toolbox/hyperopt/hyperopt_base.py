import time
import os
import shutil
import json
import copy
import numpy as np
import logging
from typing import Union, List
from pprint import pformat

from .hyperlogger import HyperoptLogger
from ..experiment import spawn_multiple_configs
from ..utils import (load_json_config,
                     load_meta_log,
                     print_framed,
                     merge_hdf5_files)


class BaseHyperOptimisation(object):
    """
    Base Class for Running Hyperparameter Optimisation Searches
    - Assumes that func_to_eval takes 3 inputs:
        1. "net_config": Dict with relevant network details (see BodyBuilder)
        2. "train_config": Dict with relevant training details
        3. "log_config": Dict with relevant logging details
    - Note that the combination of the two inputs depends on your computational
      ressouces. I.e. 4 RTX 2080 might fit 3 models per GPU (12 total) = 3 evals
      + 4 batch size/parallel configs might be a good usage
    - The input "search_params" provides a dict with parameters and their
      ranges to search over - construct space in specific hyperopt instance
    - The input "problem_type" specifies how to evaluate the training run
    """
    def __init__(self,
                 hyper_log: HyperoptLogger,
                 resource_to_run: str,
                 job_arguments: dict,
                 config_fname: str,
                 job_fname: str,
                 experiment_dir: str,
                 search_params: dict,
                 search_type: str="grid",
                 search_schedule: str="sync"):
        # Set up the random hyperparameter search run
        self.hyper_log = hyper_log                    # Hyperopt. Log Instance
        self.resource_to_run = resource_to_run        # Compute resource to run
        self.config_fname = config_fname              # Fname base config file
        self.base_config = load_json_config(config_fname)  # Base Train Config
        self.job_fname = job_fname                    # Python file to run job
        self.job_arguments = job_arguments            # SGE job info
        self.experiment_dir = experiment_dir          # Where to store all logs
        if self.experiment_dir[-1] != "/":
            self.experiment_dir += "/"

        # Create the directory if it doesn't exist yet
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)

        # Copy over base config .json file -  to be copied + modified in search
        config_copy = os.path.join(self.experiment_dir,
                                   "search_base_config.json")
        if not os.path.exists(config_copy):
            shutil.copy(config_fname, config_copy)

        # Key Input: Specify which params to optimize & in which ranges (dict)
        self.search_params = search_params            # param space specs
        self.search_type = search_type                # random/grid/smbo
        self.search_schedule = search_schedule        # sync vs async jobs
        self.current_iter = len(hyper_log)            # get previous number its

    def run_search(self,
                   num_search_batches: Union[None, int] = None,
                   num_evals_per_batch: Union[None, int] = None,
                   num_total_evals: Union[None, int] = None,
                   num_running_evals: Union[None, int] = None,
                   num_seeds_per_eval: Union[None, int] = 1):
        """
        Run a hyperparameter search: Random, Grid, SMBO
        Differentiate between synchronous and asynchronous launching of jobs
        - Sync: Run batches of evaluations. Only spawn new jobs once batch done
                => Num Batches X Evals/Batch X Seed/Eval
        - Async: Run constant number of jobs at all times. Respawn once 'slot'
                 becomes available. Benefit of constant resource utilisation
                => Num Total Evals - Constrain: Running Evals X Seed/Eval
        """
        # Check that right inputs provided for sync vs async job scheduling
        if self.search_schedule == "sync":
            assert type(num_search_batches) == int, "Provide valid 'sync' input"
            assert type(num_evals_per_batch) == int, "Provide valid 'sync' input"
        elif self.search_schedule == "async":
            assert type(num_total_evals) == int, "Provide valid 'async' input"
            assert type(num_running_evals) == int, "Provide valid 'async' input"
        else:
            raise ValueError("Provide valid schedule type ('sync', 'async')"
                             + " for search.")

        # Log the beginning of multiple config experiments
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info(f"Hyperoptimisation ({self.search_schedule} - " +
                         f"{self.search_type}) Run - Range of Parameters:")
        for line in pformat(self.search_params.toDict()).split('\n'):
            self.logger.info(line)

        # Start Launching Jobs Depending on the Scheduling Setup
        if self.search_schedule == "sync":
            self.logger.info(f"Total Search Batches: {num_search_batches} |" \
                             f" Batchsize: {num_evals_per_batch} |" \
                             f" Seeds/Eval: {num_seeds_per_eval}")
            print_framed(f"START HYPEROPT RUNS")
            if self.hyper_log.no_results_logging:
                self.logger.info(f"!!!WARNING!!!: No metrics hyperopt logging!")
            self.run_sync_search(num_search_batches,
                                 num_evals_per_batch,
                                 num_seeds_per_eval)
        else:
            self.logger.info(f"Total Search Jobs: {num_total_evals} |" \
                             f" Running Job Limit: {num_running_evals} |" \
                             f" Seeds/Eval: {num_seeds_per_eval}")
            print_framed(f"START HYPEROPT RUNS")
            if self.hyper_log.no_results_logging:
                self.logger.info(f"!!!WARNING!!!: No metrics hyperopt logging!")
            self.run_async_search(num_total_evals,
                                  num_running_evals,
                                  num_seeds_per_eval)

    def run_async_search(self,
                        num_total_evals: int,
                        num_running_evals: int,
                        num_seeds_per_eval: Union[None, int] = 1):
        """ Run jobs asynchronously - launch whenever resource available. """
        '''
        # Does not work with Batch SMBO since proposals rely on GP!
        assert self.search_type != "smbo", "Async scheduling does not support SMBO"
        completed_evals, running_evals = 0, 0
        running_eval_ids = []

        # Spawn 1st batch of evals until limit of allowed usage is reached
        while running_evals < min(num_running_evals, num_total_evals):
            proposal = self.get_hyperparam_proposal(1)
            eval_config = self.gen_hyperparam_configs(proposal)
            fname, eval_id = self.write_configs_to_json(eval_config)
            # Note that we only control evals and not individual jobs!
            job_ids = spawn_multiple_seeds_experiment(
                                   resource_to_run=self.resource_to_run,
                                   job_filename=self.job_fname,
                                   config_filenames=fname,
                                   job_arguments=self.job_arguments,
                                   experiment_dir=self.experiment_dir,
                                   num_seeds=num_seeds_per_eval,
                                   logger_level=logging.WARNING)
            running_eval_ids.append(job_id)
            running_evals += 1

        # Run experiment until num_total_evals jobs are completed
        while completed_jobs < num_total_evals:
            # Once budget is fully allocated - start monitor running jobs
            while running_evals == num_running_evals:
                for job_id in running_eval_ids:
                    status = monitor(job_ids)
                    if status == 0:
                        completed_evals += 1
                        running_evals -= 1
                        running_job_ids.remove(job_id)

                # Once budget becomes available again - fill up with new jobs
                while running_evals < min(num_running_evals,
                                          num_total_evals - completed_jobs):
                    proposal = self.get_hyperparam_proposal(1)
                    eval_config = self.gen_hyperparam_configs(proposal)
                    fname, eval_id = self.write_configs_to_json(eval_config)
                    job_id = spawn_jobs(fname)
                    running_eval_ids.append(job_id)
                    running_evals += 1
        '''

    def run_sync_search(self,
                        num_search_batches: int,
                        num_evals_per_batch: int,
                        num_seeds_per_eval: Union[None, int] = 1):
        """ Run synchronous batches of jobs in a loop. """
        # Only run the batch loop for the remaining iterations
        self.current_iter = int(self.current_iter/num_evals_per_batch)
        for search_iter in range(num_search_batches - self.current_iter):
            start_t = time.time()
            # Update the hyperopt iteration counter
            self.current_iter += 1

            # Get a set of hyperparameters & plug them into config dicts
            batch_proposals = self.get_hyperparam_proposal(num_evals_per_batch)
            batch_configs = self.gen_hyperparam_configs(batch_proposals)
            batch_fnames, run_ids = self.write_configs_to_json(batch_configs)

            self.logger.info(f"START - {self.current_iter}/" \
                             f"{num_search_batches} batch of" \
                             f" hyperparameters - {num_seeds_per_eval} seeds")

            # Training w. prev. specified hyperparams & evaluate, get time taken
            batch_results_dirs = self.train_hyperparams(batch_fnames,
                                                        num_seeds_per_eval)

            self.logger.info(f"DONE - {self.current_iter}/" \
                             f"{num_search_batches} batch of" \
                             f" hyperparameters - {num_seeds_per_eval} seeds")
            time_elapsed = time.time() - start_t

            # Attempt merging of hyperlogs - until successful!
            if not self.hyper_log.no_results_logging:
                while True:
                    try:
                        meta_eval_log = self.get_meta_eval_log(
                                            self.hyper_log.all_run_ids
                                            + run_ids)
                        break
                    except:
                        time.sleep(1)
                        continue

                self.logger.info(f"MERGE - {self.current_iter}/" \
                                 f"{num_search_batches} batch of " \
                                 f"hyperparameters - {num_seeds_per_eval} seeds")

                # Get performance score, update & save hypersearch log
                perf_measures = self.hyper_log.update_log(batch_proposals,
                                                          meta_eval_log,
                                                          time_elapsed,
                                                          run_ids)
                self.clean_up_after_batch_iteration(batch_proposals,
                                                    perf_measures)
            else:
                # Log without collected results
                self.hyper_log.update_log(batch_proposals, None,
                                          None, time_elapsed, run_ids)
                self.logger.info(f"UPDATE - {self.current_iter}/" \
                                 f"{num_search_batches} batch of " \
                                 f"hyperparameters - {num_seeds_per_eval} seeds")

            self.hyper_log.save_log()
            print_framed(f"COMPLETED BATCH {self.current_iter}/" \
                         f"{num_search_batches}")

    def get_hyperparam_proposal(self, num_iter_batch: int):
        """ Get proposals to eval - implemented by specific hyperopt algo"""
        raise NotImplementedError

    def clean_up_after_batch_iteration(self, batch_proposals, perf_measures):
        """ Perform post-iteration clean-up. (E.g. update surrogate model) """
        return

    def gen_hyperparam_configs(self, proposals: list):
        """ Generate config file for a specific proposal to evaluate """
        config_params_batch = []
        # Sample a new configuration for each eval in the batch
        for s_id in range(len(proposals)):
            sample_config = copy.deepcopy(self.base_config)

            # Construct config dicts individually - set params in train config
            for param_name, param_value in proposals[s_id].items():
                sample_config.train_config[param_name] = param_value

            # # TODO: Differentiate between network and train config variable?!
            # for param_name, param_value in proposals[s_id].items():
            #     config_id, param = param_name.split(":")
            #     if config_id == "train":
            #         sample_config.train_config[param] = param_value
            #     elif config_id == "network":
            #         sample_config.network_config[param] = param_value

            # Add param configs to batch lists
            config_params_batch.append(sample_config)
        return config_params_batch

    def write_configs_to_json(self, config_params_batch: list):
        """ Take batch-list of configs & write to jsons. Return fnames. """
        # Init list of config filenames to exec & base string for postproc
        config_fnames_batch = []
        all_run_ids = []

        for s_id in range(len(config_params_batch)):
            run_id = "b_" + str(self.current_iter) + "_eval_" + str(s_id)
            s_config_fname = os.path.join(self.experiment_dir,
                                          run_id + '.json')

            # Write config dictionary to json file
            with open(s_config_fname, 'w') as f:
                json.dump(config_params_batch[s_id], f)

            # Add config fnames to batch lists
            config_fnames_batch.append(s_config_fname)
            all_run_ids.append(run_id)

        return config_fnames_batch, all_run_ids

    def train_hyperparams(self, batch_fnames: list,
                          num_seeds_per_eval: Union[None, int] = None):
        """ Train the network for a batch of hyperparam configs """
        # Spawn the batch of synchronous evaluations
        spawn_multiple_configs(resource_to_run=self.resource_to_run,
                               job_filename=self.job_fname,
                               config_filenames=batch_fnames,
                               job_arguments=self.job_arguments,
                               experiment_dir=self.experiment_dir,
                               num_seeds=num_seeds_per_eval,
                               logger_level=logging.WARNING)

        # Clean up config files (redundant see experiment sub-folder)
        for f in batch_fnames:
            os.remove(f)

    def get_meta_eval_log(self, all_run_ids):
        """ Scavenge the experiment dictonaries & load in logs. """
        all_folders = [x[0] for x in os.walk(self.experiment_dir)][1:]
        # Get rid of timestring in beginning & collect all folders/hdf5 files
        hyperp_results_folder = []
        # Need to make sure that run_ids & experiment folder match!
        for run_id in all_run_ids:
            for f in all_folders:
                if f[len(self.experiment_dir) + 9:] == run_id:
                    hyperp_results_folder.append(f)
                    continue

        # Collect all paths to the .hdf5 file
        log_paths = []
        for i in range(len(hyperp_results_folder)):
            log_d_t = os.path.join(hyperp_results_folder[i], "logs/")
            for file in os.listdir(log_d_t):
                fname, fext = os.path.splitext(file)
                if file.endswith(".hdf5") and fname in all_run_ids:
                    log_paths.append(os.path.join(log_d_t, file))

        # Merge individual run results into a single hdf5 file
        meta_log_fname = os.path.join(self.experiment_dir, "meta_log.hdf5")

        assert len(log_paths) == len(all_run_ids)

        merge_hdf5_files(meta_log_fname, log_paths,
                         file_ids=all_run_ids)

        # Load in meta-results log with values meaned over seeds
        meta_eval_logs = load_meta_log(meta_log_fname, mean_seeds=True)
        return meta_eval_logs
