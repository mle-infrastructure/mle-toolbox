import time
import os
import shutil
import json
import copy
import numpy as np
import logging
from typing import Union, List
from pprint import pformat

from .hyperopt_logger import HyperoptLogger
from ..experiment import spawn_multiple_configs
from ..utils import load_json_config, load_meta_log, print_framed
from ..utils.manipulate_files import merge_hdf5_files


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
    - The input "params_to_search" provides a dict with parameters and their
      ranges to search over - construct space in specific hyperopt instance
    - The input "problem_type" specifies how to evaluate the training run
    """
    def __init__(self,
                 hyper_log: HyperoptLogger,
                 job_arguments: dict,
                 config_fname: str,
                 job_fname: str,
                 experiment_dir: str,
                 params_to_search: dict,
                 problem_type: str,
                 eval_metrics: Union[str, List[str]]):
        # Set up the random hyperparameter search run
        self.hyper_log = hyper_log                    # Hyperopt. Log Instance
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
        self.params_to_search = params_to_search
        self.current_iter = len(hyper_log)            # get prev its

        # Problem - set up eval: {"best", "final"}
        self.problem_type = problem_type
        self.eval_metrics = eval_metrics
        if type(self.eval_metrics) == str:
            self.eval_metrics = [self.eval_metrics]
        # NOTE: Need to generate self.param_range in specific hyperopt instance

    def run_search(self,
                   num_search_batches: int,
                   num_iter_per_batch: int,
                   num_evals_per_iter: Union[None, int] = None):
        """ Run the search for a number of batch iterations. """
        # Log the beginning of multiple config experiments
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.logger.info("Hyperoptimisation Run - Range of Parameters:")
        for line in pformat(self.params_to_search.toDict()).split('\n'):
            self.logger.info(line)
        self.logger.info(f"Total No. Search Batches: {num_search_batches} |" \
                         f" Batchsize: {num_iter_per_batch} |" \
                         f" Evaluations: {num_evals_per_iter}")

        # Only run the batch loop for the remaining iterations
        self.current_iter = int(self.current_iter/num_iter_per_batch)
        for search_iter in range(num_search_batches - self.current_iter):
            start_t = time.time()
            # Update the hyperopt iteration counter
            self.current_iter += 1

            # Get a set of hyperparameters & plug them into config dicts
            batch_proposals = self.get_hyperparam_proposal(num_iter_per_batch)
            batch_configs = self.gen_hyperparam_configs(batch_proposals)
            batch_fnames, run_ids = self.write_configs_to_json(batch_configs)

            self.logger.info(f"START - {self.current_iter}/{num_search_batches} batch of" \
                             f" hyperparameters - {num_evals_per_iter} seeds")

            # Training w. prev. specified hyperparams & evaluate, get time taken
            batch_results_dirs = self.train_hyperparams(batch_fnames,
                                                        num_evals_per_iter)

            self.logger.info(f"DONE - {self.current_iter}/{num_search_batches} batch of" \
                             f" hyperparameters - {num_evals_per_iter} seeds")

            # Attempt merging of hyperlogs - until successful!
            while True:
                try:
                    meta_eval_log = self.get_meta_eval_log(self.hyper_log.all_run_ids + run_ids)
                    break
                except:
                    time.sleep(1)
                    continue

            perf_measures = self.evaluate_hyperparams(meta_eval_log, run_ids)
            time_elapsed = time.time() - start_t

            self.logger.info(f"MERGE - {self.current_iter}/{num_search_batches} batch of" \
                             f" hyperparameters - {num_evals_per_iter} seeds")

            # Update & save the Hyperparam Optimisation Log
            self.hyper_log.update_log(batch_proposals, meta_eval_log,
                                      perf_measures, time_elapsed, run_ids)
            self.hyper_log.save_log()
            self.clean_up_after_batch_iteration(batch_proposals, perf_measures)
            print_framed(f"COMPLETED BATCH {self.current_iter}/{num_search_batches}")

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
            s_config_fname = os.path.join(self.experiment_dir, run_id + '.json')

            # Write config dictionary to json file
            with open(s_config_fname, 'w') as f:
                json.dump(config_params_batch[s_id], f)

            # Add config fnames to batch lists
            config_fnames_batch.append(s_config_fname)
            all_run_ids.append(run_id)

        return config_fnames_batch, all_run_ids

    def train_hyperparams(self, batch_fnames: list,
                          num_evals_per_iter: Union[None, int] = None):
        """ Train the network for a batch of hyperparam configs """
        # Spawn the batch of synchronous evaluations
        spawn_multiple_configs(job_filename=self.job_fname,
                               config_filenames=batch_fnames,
                               job_arguments=self.job_arguments,
                               experiment_dir=self.experiment_dir,
                               num_seeds=num_evals_per_iter,
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
                if file.endswith(".hdf5"):
                    log_paths.append(os.path.join(log_d_t, file))

        # Merge individual run results into a single hdf5 file
        meta_log_fname = os.path.join(self.experiment_dir, "meta_log.hdf5")
        assert len(log_paths) == len(all_run_ids)

        merge_hdf5_files(meta_log_fname, log_paths,
                         file_ids=all_run_ids)

        # Load in meta-results log with values meaned over seeds
        meta_eval_logs = load_meta_log(meta_log_fname, mean_seeds=True)
        return meta_eval_logs

    def evaluate_hyperparams(self, eval_logs, run_ids):
        """ Run the search for a number of iterations """
        if self.problem_type == "final":
            # Get final training loss as performance score
            perf_scores = evaluate_final_score(eval_logs,
                                               measure_keys=self.eval_metrics,
                                               run_ids=run_ids)
        elif self.problem_type == "best":
            # Get final training loss as performance score
            perf_scores = evaluate_best_score(eval_logs,
                                              measure_keys=self.eval_metrics,
                                              run_ids=run_ids)
        else:
            raise ValueError
        return perf_scores


def evaluate_final_score(eval_logs, measure_keys=["train_loss"],
                         run_ids=None):
    """
    IN: Evaluation df of evaluation, what key to use for evaluation
    OUT: dict of final scores at end of training for all metrics
    """
    perf_per_metric = {}
    for metric in measure_keys:
        int_out = {}
        for run in run_ids:
            int_out[run] = eval_logs[run]["stats"][metric]["mean"][-1]
        perf_per_metric[metric] = int_out
    return perf_per_metric


def evaluate_best_score(eval_logs, measure_keys=["train_loss"],
                        run_ids=None, max_objective=True):
    """
    IN: Evaluation df of evaluation, what key to use for evaluation
    OUT: dict of best scores during course of training for all metrics
    """
    perf_per_metric = {}
    for metric in measure_keys:
        int_out = {}
        for run in run_ids:
            if max_objective:
                int_out[run] = np.max(
                    eval_logs[run_ids[i]]["stats"][metric]["mean"])
            else:
                int_out[run] = np.min(
                    eval_logs[run_ids[i]]["stats"][metric]["mean"])
        perf_per_metric[metric] = int_out
    return perf_per_metric
