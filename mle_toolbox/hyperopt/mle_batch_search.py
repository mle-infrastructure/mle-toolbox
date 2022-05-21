import time
import os
import shutil
import copy
import logging
import numpy as np
from typing import Union, List
from .hyper_logger import HyperoptLogger
from ..utils import print_framed
from mle_logging import merge_config_logs, load_log, load_config
from mle_scheduler import MLEQueue
from mle_monitor import MLEProtocol
from mle_hyperopt import Strategies
from mle_hyperopt.utils import write_configs, merge_config_dicts
from mle_toolbox import mle_config, check_single_job_args


class MLE_BatchSearch(object):
    def __init__(
        self,
        hyper_log: HyperoptLogger,
        resource_to_run: str,
        job_arguments: dict,
        config_fname: str,
        job_fname: str,
        experiment_dir: str,
        search_params: dict,
        search_type: str = "Grid",
        search_schedule: str = "sync",
        search_config: Union[None, dict] = None,
        message_id: Union[str, None] = None,
        protocol_db: Union[MLEProtocol, None] = None,
        debug_mode: bool = False,
    ):
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
        # Set up the hyperparameter search run
        self.hyper_log = hyper_log  # Hyperopt. Log Instance
        self.resource_to_run = resource_to_run  # Compute resource to run
        self.config_fname = config_fname  # Fname base config file
        # Load base config of jobs to be manipulated by search
        fname, self.config_fext = os.path.splitext(config_fname)
        self.base_config = load_config(config_fname, return_dotmap=True)

        self.job_fname = job_fname  # Python file to run job
        # 0. Check if all required args are given - otw. add default to copy
        self.job_arguments = check_single_job_args(
            resource_to_run, job_arguments.copy()
        )
        self.experiment_dir = experiment_dir  # Where to store all logs
        if self.experiment_dir[-1] != "/":
            self.experiment_dir += "/"

        # Create the directory if it doesn't exist yet & set log json name
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)
        self.search_log_path = os.path.join(
            self.experiment_dir, "search_log.yaml"
        )

        # Copy over base config .json file -  to be copied + modified in search
        config_copy = os.path.join(
            self.experiment_dir, "search_base_config" + self.config_fext
        )
        if not os.path.exists(config_copy):
            shutil.copy(config_fname, config_copy)

        # Key Input: Specify which params to optimize & in which ranges (dict)
        self.search_params = search_params  # param space specs
        self.search_type = search_type  # random/grid/smbo/etc.
        self.search_schedule = search_schedule  # sync vs async jobs
        self.current_iter = len(hyper_log)  # get previous number its

        # Store message id for slack cluster bot & protocol db
        self.message_id = message_id
        self.protocol_db = protocol_db

        # Debug mode for queue - keep around log/err
        self.debug_mode = debug_mode

        # Setup the search strategy
        assert self.search_type in [
            "Grid",
            "Random",
            "SMBO",
            "Coordinate",
            "Nevergrad",
            "PBT",
            "Halving",
            "Hyperband",
        ]

        self.strategy = Strategies[search_type](
            **search_params,
            search_config=search_config,
            maximize_objective=hyper_log.max_objective,
            seed_id=mle_config.general.random_seed,
            verbose=True,
        )

        # Reload data to strategy if applicable
        if self.hyper_log.reloaded:
            self.strategy.load(self.search_log_path)

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
            assert type(num_evals_per_batch) in [
                int,
                list,
            ], "Provide valid sync input"
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
                max_running_jobs,
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
                num_total_evals,
                max_running_jobs,
                num_seeds_per_eval,
                random_seeds,
            )

    def run_async_search(
        self,
        num_total_evals: int,
        max_running_jobs: Union[int, None] = None,
        num_seeds_per_eval: int = 1,
        random_seeds: Union[None, List[int]] = None,
    ):
        """Run jobs asynchronously - launch whenever resource available."""
        # Does not work with Batch SMBO since proposals rely on GP!
        assert self.search_type != "smbo", "Async scheduling - No SMBO support"
        # Get all hyperparameters & plug them into config dicts, store jsons
        batch_proposals = self.ask(num_total_evals)
        # Ensure that batch_proposals is a list for single config case
        if type(batch_proposals) == dict:
            batch_proposals = [batch_proposals]
        batch_configs = self.gen_hyperparam_configs(batch_proposals)
        batch_fnames, run_ids = self.write_configs_to_file(batch_configs)

        # Generate a queue of jobs to launch and work through them
        # Different seed logs are merged within queue whenever all completed
        self.logger.info(
            f"START - {num_total_evals} Eval Configs - "
            f"{max_running_jobs} Jobs at a Time -"
            f" {num_seeds_per_eval} Seeds"
        )
        start_t = time.time()
        job_queue = MLEQueue(
            resource_to_run=self.resource_to_run,
            job_filename=self.job_fname,
            job_arguments=self.job_arguments,
            config_filenames=batch_fnames,
            experiment_dir=self.experiment_dir,
            num_seeds=num_seeds_per_eval,
            random_seeds=random_seeds,
            max_running_jobs=max_running_jobs,
            cloud_settings=mle_config.gcp,
            automerge_configs=True,
            use_slack_bot=(self.message_id is not None),
            slack_message_id=self.message_id,
            slack_user_name=mle_config.slack.user_name,
            slack_auth_token=mle_config.slack.slack_token,
            protocol_db=self.protocol_db,
            debug_mode=self.debug_mode,
        )
        job_queue.run()
        time_elapsed = time.time() - start_t

        self.logger.info(
            f"DONE - {num_total_evals} Eval Configs - "
            f"{max_running_jobs} Jobs at a Time -"
            f" {num_seeds_per_eval} Seeds"
        )

        # Update + save hyperlog after merging eval log .hdf5 files
        perf_measures, ckpts = self.update_hyper_log(
            batch_proposals, run_ids, time_elapsed, num_seeds_per_eval
        )
        self.hyper_log.save_log()

        # Clean up after search batch iteration
        self.tell(run_ids, batch_proposals, perf_measures, ckpts)
        for f in batch_fnames:
            os.remove(f)
        print_framed(f"COMPLETED QUEUE CLEAN-UP {num_total_evals} EVALS")

    def run_sync_search(
        self,
        num_search_batches: int,
        num_evals_per_batch: Union[int, List[int]],
        num_seeds_per_eval: Union[None, int] = 1,
        max_running_jobs: Union[None, int] = None,
        random_seeds: Union[None, List[int]] = None,
    ):
        """Run synchronous batches of jobs in a loop."""
        # Only run the batch loop for the remaining iterations
        if type(num_evals_per_batch) == int:
            prev_batches = int(self.current_iter / num_evals_per_batch)
            self.current_iter = int(self.current_iter / num_evals_per_batch)
        else:
            # TODO: Can't reload hyperband/halving at this moment!
            self.current_iter = 0
            prev_batches = 0

        for search_iter in range(num_search_batches):
            # Update the hyperopt iteration counter
            self.current_iter += 1

            # Get a set of hyperparameters & plug them into config dicts
            # Note: num_evals_per_batch doesn't affect PBT/Halving/Hyperband
            batch_proposals = self.ask(num_evals_per_batch)
            # Ensure that batch_proposals is a list for single config case
            if type(batch_proposals) == dict:
                batch_proposals = [batch_proposals]
            batch_configs = self.gen_hyperparam_configs(batch_proposals)
            batch_fnames, run_ids = self.write_configs_to_file(batch_configs)

            self.logger.info(
                f"START - {self.current_iter}/"
                f"{num_search_batches + prev_batches} Batch of"
                f" Hyperparameters - {num_seeds_per_eval} Seeds"
            )

            # Training w. prev. specified hyperparams & eval, get time taken
            if (
                type(num_evals_per_batch) == int
                and max_running_jobs is not None
            ):
                max_jobs = num_seeds_per_eval * num_evals_per_batch
            else:
                max_jobs = max_running_jobs

            start_t = time.time()
            job_queue = MLEQueue(
                self.resource_to_run,
                self.job_fname,
                self.job_arguments,
                batch_fnames,
                self.experiment_dir,
                num_seeds_per_eval,
                random_seeds=random_seeds,
                max_running_jobs=max_jobs,
                debug_mode=True,
                cloud_settings=mle_config.gcp,
                use_slack_bot=(self.message_id is not None),
                slack_message_id=self.message_id,
                slack_user_name=mle_config.slack.user_name,
                slack_auth_token=mle_config.slack.slack_token,
                protocol_db=self.protocol_db,
                automerge_configs=True,
            )
            job_queue.run()
            time_elapsed = time.time() - start_t
            self.logger.info(
                f"DONE - {self.current_iter}/"
                f"{num_search_batches + prev_batches} Batch of"
                f" Hyperparameters - {num_seeds_per_eval} Seeds"
            )
            time_elapsed = time.time() - start_t

            # Overwrite provided seeds with the ones sampled in the JobQueue
            # Otherwise this will resample seeds which will cause problems
            # when aggregating the different logs across batch iterations
            # Potential danger: Overfitting of one specific seed?
            random_seeds = job_queue.random_seeds

            # Update + save hyperlog after merging eval log .hdf5 files
            perf_measures, ckpts = self.update_hyper_log(
                batch_proposals, run_ids, time_elapsed, num_seeds_per_eval
            )
            self.hyper_log.save_log()

            # Clean up after search batch iteration - delete redundant configs
            self.tell(run_ids, batch_proposals, perf_measures, ckpts)
            for f in batch_fnames:
                os.remove(f)
            print_framed(
                f"COMPLETED BATCH CLEAN-UP {self.current_iter}/"
                f"{num_search_batches + prev_batches}"
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
                        self.experiment_dir,
                        self.hyper_log.all_run_ids + run_ids,
                    )
                    # Load in meta-results log with values meaned over seeds
                    meta_log_fname = os.path.join(
                        self.experiment_dir, "meta_log.hdf5"
                    )
                    meta_eval_log = load_log(
                        meta_log_fname, aggregate_seeds=True
                    )
                    break
                except Exception:
                    time.sleep(1)
                    continue

            self.logger.info(
                f"MERGE - {len(run_ids)} Eval Configs of "
                f"Hyperparameters - {num_seeds_per_eval} Seeds"
            )

            # Get performance score, update & save hypersearch log
            perf_measures, ckpts = self.hyper_log.update_log(
                batch_proposals, meta_eval_log, time_elapsed, run_ids
            )
        else:
            # Log without collected results - perf_measures None output
            perf_measures, ckpts = self.hyper_log.update_log(
                batch_proposals, None, time_elapsed, run_ids
            )
            self.logger.info(
                f"UPDATE - {len(run_ids)} Eval Configs of "
                f"Hyperparameters - {num_seeds_per_eval} Seeds"
            )
        return perf_measures, ckpts

    def ask(self, num_iter_batch: int):
        """Get proposals to eval - implemented by specific hyperopt algo"""
        return self.strategy.ask(num_iter_batch)

    def tell(
        self,
        run_ids: list,
        batch_proposals: list,
        perf_measures: dict,
        ckpts: Union[list, None],
    ):
        """Perform post-iteration clean-up. (E.g. update surrogate model)"""
        proposals, measures = [], []
        # Collect all performance data for strategy update
        for i, id in enumerate(run_ids):
            proposals.append(batch_proposals[i])
            metrics = []
            for k in self.hyper_log.eval_metrics:
                # Differentiate between max and min of evaluation metric
                effective_perf = perf_measures[k][id]
                # If we use surrogate model - select variables to be modelled
                if self.search_type == "SMBO":
                    if k == self.strategy.search_config["metric_to_model"]:
                        metrics = effective_perf
                elif (
                    self.search_type == "Nevergrad"
                    and "metric_to_model" in self.strategy.search_config.keys()
                ):
                    if k == self.strategy.search_config["metric_to_model"]:
                        metrics = effective_perf
                else:
                    metrics.append(effective_perf)
            measures.append(metrics)
        self.strategy.tell(
            proposals, np.array(measures).squeeze().tolist(), ckpts
        )
        self.strategy.save(self.search_log_path)

    def gen_hyperparam_configs(self, proposals: list):
        """Generate config file for a specific proposal to evaluate"""
        config_params_batch = []
        # Sample a new configuration for each eval in the batch
        for s_id in range(len(proposals)):
            sample_config = copy.deepcopy(self.base_config)
            # Construct config dicts individually - set params in train config
            for param_name, param_value in proposals[s_id].items():
                # Differentiate between model_config & train_config params
                if "train_config" in sample_config.keys():
                    try:
                        config_id, param = param_name.split(":")
                        if config_id == "train":
                            sample_config.train_config[param] = param_value
                        elif config_id == "model":
                            sample_config.model_config[param] = param_value
                    except Exception:
                        # Merge nested config dictionaries
                        if type(param_value) == dict:
                            sample_config.train_config[param_name] = dict(
                                merge_config_dicts(
                                    sample_config.train_config[param_name],
                                    param_value,
                                )
                            )
                        else:
                            sample_config.train_config[param_name] = param_value
                else:
                    sample_config[param_name] = param_value
            # Add param configs to batch lists
            config_params_batch.append(sample_config)
        return config_params_batch

    def write_configs_to_file(self, config_params_batch: list):
        """Take batch-list of configs & write to jsons. Return fnames."""
        # Init list of config filenames to exec & base string for postproc
        params_batch, config_fnames_batch, all_run_ids = [], [], []
        for s_id in range(len(config_params_batch)):
            run_id = "b_" + str(self.current_iter) + "_eval_" + str(s_id)
            s_config_fname = os.path.join(
                self.experiment_dir, run_id + self.config_fext
            )
            params_batch.append(config_params_batch[s_id].toDict())
            config_fnames_batch.append(s_config_fname)
            all_run_ids.append(run_id)
        write_configs(params_batch, config_fnames_batch)
        return config_fnames_batch, all_run_ids
