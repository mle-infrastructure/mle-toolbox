import time
import os
import shutil
import json
import copy
import logging
from typing import Union, List
from pprint import pformat

from .hyper_logger import HyperoptLogger
from ..job import JobQueue
from ..utils import load_json_config, print_framed
from mle_logging import merge_config_logs, load_meta_log


class BaseHyperOptimisation(object):
    """
    Base Class for Running Hyperparameter Optimisation Searches
    - Assumes that func_to_eval takes 3 inputs:
        1. "model_config": Dict with relevant model details
        2. "train_config": Dict with relevant training details
        3. "log_config": Dict with relevant logging details
    - The input "search_params" provides a dict with parameters and their
      ranges to search over - construct space in specific hyperopt instance
    - The input "problem_type" specifies how to evaluate the training run
    """

    def __init__(
        self,
        hyper_log: HyperoptLogger,
        resource_to_run: str,
        job_arguments: dict,
        config_fname: str,
        job_fname: str,
        experiment_dir: str,
        search_params: dict,
        search_type: str = "grid",
        search_schedule: str = "sync",
        message_id: Union[str, None] = None,
    ):
        # Set up the hyperparameter search run
        self.hyper_log = hyper_log  # Hyperopt. Log Instance
        self.resource_to_run = resource_to_run  # Compute resource to run
        self.config_fname = config_fname  # Fname base config file
        self.base_config = load_json_config(config_fname)  # Base Train Config
        self.job_fname = job_fname  # Python file to run job
        self.job_arguments = job_arguments  # SGE job info
        self.experiment_dir = experiment_dir  # Where to store all logs
        if self.experiment_dir[-1] != "/":
            self.experiment_dir += "/"

        # Create the directory if it doesn't exist yet
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)

        # Copy over base config .json file -  to be copied + modified in search
        config_copy = os.path.join(self.experiment_dir, "search_base_config.json")
        if not os.path.exists(config_copy):
            shutil.copy(config_fname, config_copy)

        # Key Input: Specify which params to optimize & in which ranges (dict)
        self.search_params = search_params  # param space specs
        self.search_type = search_type  # random/grid/smbo
        self.search_schedule = search_schedule  # sync vs async jobs
        self.current_iter = len(hyper_log)  # get previous number its

        # Store message id for slack cluster bot
        self.message_id = message_id

    def run_search(
        self,
        num_search_batches: Union[None, int] = None,
        num_evals_per_batch: Union[None, int] = None,
        num_total_evals: Union[None, int] = None,
        max_running_jobs: Union[None, int] = None,
        num_seeds_per_eval: Union[None, int] = 1,
        random_seeds: Union[None, List[int]] = None,
    ):
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
            assert type(num_search_batches) == int, "Provide valid sync input"
            assert type(num_evals_per_batch) == int, "Provide valid sync input"
        elif self.search_schedule == "async":
            assert type(num_total_evals) == int, "Provide valid 'async' input"
            assert type(max_running_jobs) == int, "Provide valid 'async' input"
        else:
            raise ValueError(
                "Provide valid schedule type ('sync', 'async')" + " for search."
            )

        # Log the beginning of multiple config experiments
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info(
            f"Hyperoptimisation ({self.search_schedule} - "
            + f"{self.search_type}) Run - Range of Parameters:"
        )
        for line in pformat(self.search_params).split("\n"):
            self.logger.info(line)

        # Start Launching Jobs Depending on the Scheduling Setup
        if self.search_schedule == "sync":
            self.logger.info(
                f"Total Search Batches: {num_search_batches} |"
                f" Batchsize: {num_evals_per_batch} |"
                f" Seeds/Eval: {num_seeds_per_eval}"
            )
            print_framed("START HYPEROPT RUNS")
            if self.hyper_log.no_results_logging:
                self.logger.info("!!!WARNING!!!: No metrics hyperopt logging!")
            self.run_sync_search(
                num_search_batches,
                num_evals_per_batch,
                num_seeds_per_eval,
                random_seeds,
            )
        else:
            self.logger.info(
                f"Total Search Evals: {num_total_evals} |"
                f" Running Job Limit: {max_running_jobs} |"
                f" Seeds/Eval: {num_seeds_per_eval}"
            )
            print_framed("START HYPEROPT RUNS")
            if self.hyper_log.no_results_logging:
                self.logger.info("!!!WARNING!!!: No metrics hyperopt logging!")
            self.run_async_search(
                num_total_evals, max_running_jobs, num_seeds_per_eval, random_seeds
            )

    def run_async_search(
        self,
        num_total_evals: int,
        max_running_jobs: int,
        num_seeds_per_eval: int = 1,
        random_seeds: Union[None, List[int]] = None,
    ):
        """Run jobs asynchronously - launch whenever resource available."""
        # Does not work with Batch SMBO since proposals rely on GP!
        assert self.search_type != "smbo", "Async scheduling - No SMBO support"
        # Get all hyperparameters & plug them into config dicts, store jsons
        batch_proposals = self.get_hyperparam_proposal(num_total_evals)
        batch_configs = self.gen_hyperparam_configs(batch_proposals)
        batch_fnames, run_ids = self.write_configs_to_json(batch_configs)

        # Generate a queue of jobs to launch and work through them
        # Different seed logs are merged within queue whenever all completed
        self.logger.info(
            f"START - {num_total_evals} Eval Configs - "
            f"{max_running_jobs} Jobs at a Time -"
            f" {num_seeds_per_eval} Seeds"
        )
        start_t = time.time()
        job_queue = JobQueue(
            self.resource_to_run,
            self.job_fname,
            batch_fnames,
            self.job_arguments,
            self.experiment_dir,
            num_seeds_per_eval,
            random_seeds=random_seeds,
            max_running_jobs=max_running_jobs,
            message_id=self.message_id,
        )
        job_queue.run()
        time_elapsed = time.time() - start_t

        self.logger.info(
            f"DONE - {num_total_evals} Eval Configs - "
            f"{max_running_jobs} Jobs at a Time -"
            f" {num_seeds_per_eval} Seeds"
        )

        # Update + save hyperlog after merging eval log .hdf5 files
        perf_measures = self.update_hyper_log(
            batch_proposals, run_ids, time_elapsed, num_seeds_per_eval
        )
        self.hyper_log.save_log()

        # Clean up after search batch iteration
        self.clean_up_after_batch_iteration(batch_proposals, perf_measures)
        for f in batch_fnames:
            os.remove(f)
        print_framed(f"COMPLETED QUEUE CLEAN-UP {num_total_evals} EVALS")

    def run_sync_search(
        self,
        num_search_batches: int,
        num_evals_per_batch: int,
        num_seeds_per_eval: Union[None, int] = 1,
        random_seeds: Union[None, List[int]] = None,
    ):
        """Run synchronous batches of jobs in a loop."""
        # Only run the batch loop for the remaining iterations
        self.current_iter = int(self.current_iter / num_evals_per_batch)
        for search_iter in range(num_search_batches - self.current_iter):
            # Update the hyperopt iteration counter
            self.current_iter += 1

            # Get a set of hyperparameters & plug them into config dicts
            batch_proposals = self.get_hyperparam_proposal(num_evals_per_batch)
            batch_configs = self.gen_hyperparam_configs(batch_proposals)
            batch_fnames, run_ids = self.write_configs_to_json(batch_configs)

            self.logger.info(
                f"START - {self.current_iter}/"
                f"{num_search_batches} Batch of"
                f" Hyperparameters - {num_seeds_per_eval} Seeds"
            )

            # Training w. prev. specified hyperparams & eval, get time taken
            max_jobs = num_seeds_per_eval * num_evals_per_batch
            start_t = time.time()
            job_queue = JobQueue(
                self.resource_to_run,
                self.job_fname,
                batch_fnames,
                self.job_arguments,
                self.experiment_dir,
                num_seeds_per_eval,
                random_seeds=random_seeds,
                max_running_jobs=max_jobs,
                message_id=self.message_id,
            )
            job_queue.run()
            time_elapsed = time.time() - start_t
            self.logger.info(
                f"DONE - {self.current_iter}/"
                f"{num_search_batches} Batch of"
                f" Hyperparameters - {num_seeds_per_eval} Seeds"
            )
            time_elapsed = time.time() - start_t

            # Update + save hyperlog after merging eval log .hdf5 files
            perf_measures = self.update_hyper_log(
                batch_proposals, run_ids, time_elapsed, num_seeds_per_eval
            )
            self.hyper_log.save_log()

            # Clean up after search batch iteration - delete redundant configs
            self.clean_up_after_batch_iteration(batch_proposals, perf_measures)
            for f in batch_fnames:
                os.remove(f)
            print_framed(
                f"COMPLETED BATCH CLEAN-UP {self.current_iter}/" f"{num_search_batches}"
            )

    def update_hyper_log(
        self, batch_proposals, run_ids, time_elapsed, num_seeds_per_eval
    ):
        """Merge eval log .hdf5 files & update hyperlogger w. performance."""
        # Attempt merging of hyperlogs - until successful!
        if not self.hyper_log.no_results_logging:
            while True:
                try:
                    merge_config_logs(
                        self.experiment_dir, self.hyper_log.all_run_ids + run_ids
                    )
                    # Load in meta-results log with values meaned over seeds
                    meta_log_fname = os.path.join(self.experiment_dir, "meta_log.hdf5")
                    meta_eval_log = load_meta_log(meta_log_fname)
                    break
                except Exception:
                    time.sleep(1)
                    continue

            self.logger.info(
                f"MERGE - {len(run_ids)} Eval Configs of "
                f"Hyperparameters - {num_seeds_per_eval} Seeds"
            )

            # Get performance score, update & save hypersearch log
            perf_measures = self.hyper_log.update_log(
                batch_proposals, meta_eval_log, time_elapsed, run_ids
            )
        else:
            # Log without collected results - perf_measures None output
            perf_measures = self.hyper_log.update_log(
                batch_proposals, None, time_elapsed, run_ids
            )
            self.logger.info(
                f"UPDATE - {len(run_ids)} Eval Configs of "
                f"Hyperparameters - {num_seeds_per_eval} Seeds"
            )
        return perf_measures

    def get_hyperparam_proposal(self, num_iter_batch: int):
        """Get proposals to eval - implemented by specific hyperopt algo"""
        raise NotImplementedError

    def clean_up_after_batch_iteration(self, batch_proposals, perf_measures):
        """Perform post-iteration clean-up. (E.g. update surrogate model)"""
        return

    def gen_hyperparam_configs(self, proposals: list):
        """Generate config file for a specific proposal to evaluate"""
        config_params_batch = []
        # Sample a new configuration for each eval in the batch
        for s_id in range(len(proposals)):
            sample_config = copy.deepcopy(self.base_config)

            # Construct config dicts individually - set params in train config
            for param_name, param_value in proposals[s_id].items():
                # Differentiate between model_config & train_config params
                try:
                    config_id, param = param_name.split(":")
                    if config_id == "train":
                        sample_config.train_config[param] = param_value
                    elif config_id == "model":
                        sample_config.model_config[param] = param_value
                except Exception:
                    sample_config.train_config[param_name] = param_value
            # Add param configs to batch lists
            config_params_batch.append(sample_config)
        return config_params_batch

    def write_configs_to_json(self, config_params_batch: list):
        """Take batch-list of configs & write to jsons. Return fnames."""
        # Init list of config filenames to exec & base string for postproc
        config_fnames_batch = []
        all_run_ids = []

        for s_id in range(len(config_params_batch)):
            run_id = "b_" + str(self.current_iter) + "_eval_" + str(s_id)
            s_config_fname = os.path.join(self.experiment_dir, run_id + ".json")

            # Write config dictionary to json file
            with open(s_config_fname, "w") as f:
                json.dump(config_params_batch[s_id], f)

            # Add config fnames to batch lists
            config_fnames_batch.append(s_config_fname)
            all_run_ids.append(run_id)

        return config_fnames_batch, all_run_ids
