import os
import time
import numpy as np
import logging
from typing import Union
from pprint import pformat
from ..utils import load_pkl_object, save_pkl_object, print_framed


class HyperoptLogger(object):
    def __init__(self,
                 hyperlog_fname: str="hyper_log.pkl",   # .pkl name to store log
                 max_objective: bool=True,              # Max/min all metrics
                 problem_type: str="final",             # "final"/"best" score logging
                 eval_metrics: Union[str, list]=[],     # Metric names to store
                 verbose_log: bool=True,                # Print at new update
                 reload_log: bool=False,                # Reload previous log
                 no_results_logging: bool=False):       # No .hdf5 run logging
        """ Mini-class to log the  """
        self.hyperlog_fname = hyperlog_fname    # Where to save the log to
        self.max_objective = max_objective      # Max/min target (reward/loss)
        self.problem_type = problem_type        # Timepoint to consider (final/best)
        self.eval_metrics = eval_metrics        # Vars to compare across runs
        if type(self.eval_metrics) == str:
            self.eval_metrics = [self.eval_metrics]
        self.verbose_log = verbose_log          # Print results whenever update
        # Want to not log metrics? - Don't need to rely on meta_log setup
        self.no_results_logging = no_results_logging

        # Instantiate the meta-logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if reload_log:
            self.reload_log()
            self.logger.info(f"Reloaded Log with {self.iter_id} Evaluations")
            self.print_log_state()
        else:
            self.opt_log = {}               # List of dict of evals
            self.iter_id = 0                # How many iterations already eval
            self.all_run_ids = []           # All run ids of evals
            self.all_evaluated_params = []  # All evaluated parameters
        self.batch_id = 0                   # Batch evaluation tracker

    def update_log(self, params, meta_eval_log, time_elapsed, run_ids):
        """ Update  log dictionary with the most recent result dictionary """
        # Update the batch evaluation counter
        self.batch_id += 1
        if not self.no_results_logging:
            perf_measures = evaluate_hyperparams(meta_eval_log, run_ids,
                                                 self.problem_type,
                                                 self.eval_metrics)
        else:
            perf_measures = None

        # Need to account for batch case - log list of dictionaries!
        if not isinstance(params, list):
            params = list(params)

        # Define list of vars from meta data to keep also in hyper df
        meta_keys_to_track = ["log_paths", "experiment_dir",
                              "config_fname", "model_ckpt", "seeds",
                              "model_type", "fig_storage_paths"]

        # Loop over list entries and log them individually
        for iter in range(len(params)):
            self.iter_id += 1
            current_iter = {"params": params[iter],
                            "time_elapsed": time_elapsed,
                            "run_id": run_ids[iter],}
            if not self.no_results_logging:
                # Add all of the individual tracked metrics
                for k, v in perf_measures.items():
                    current_iter[k] = v[run_ids[iter]]
                # Add the meta data from the meta_eval_log
                for k in meta_keys_to_track:
                    try:
                        current_iter[k] = meta_eval_log[run_ids[iter]].meta[k]
                    except:
                        continue

                # Add collected log path (after merging seeds)
                current_iter["log_fname"] = os.path.join(
                    current_iter["experiment_dir"], "logs",
                    current_iter["run_id"] + ".hdf5")

            # Merge collected info from eval to the log
            self.opt_log[self.iter_id] = current_iter

            # Store all evaluated parameters!
            self.all_evaluated_params.append(params[iter])

        # Keep track of all results/runs sofar!
        self.all_run_ids += run_ids

        if not self.no_results_logging:
            # Update best performance tracker
            self.best_per_metric = self.get_best_performances(
                                        perf_measures.keys())

            # Print currently best evaluation
            if self.verbose_log:
                self.print_log_state()
        return perf_measures

    def print_log_state(self):
        """ Log currently best param config for each metric. """
        if self.iter_id > 0 and not self.no_results_logging:
            for i, m in enumerate(self.best_per_metric.keys()):
                print_framed(m, frame_str="-")
                self.logger.info(
            r"METRIC: {} | BEST SCORE: {:.4f} | ITER: {}/{} | PARAMS:".format(
                        m, self.best_per_metric[m]["score"],
                        self.best_per_metric[m]["run_id"],
                        self.iter_id))
                for line in pformat(self.best_per_metric[m]["params"]
                                    ).split('\n'):
                    self.logger.info(line)

    def save_log(self):
        """ Save current state of hyperparameter optimization as .pkl file """
        save_pkl_object(self.opt_log, self.hyperlog_fname)

    def reload_log(self):
        """ Reload the previously stored .pkl log file """
        try:
            self.opt_log = load_pkl_object(self.hyperlog_fname)
            self.all_evaluated_params = []
            self.all_run_ids = []
            for key, eval_iter in self.opt_log.items():
                self.all_evaluated_params.append(eval_iter["params"])
                self.all_run_ids.append(eval_iter["run_id"])
            self.iter_id = len(self.opt_log)
        except:
            self.opt_log = {}
            self.iter_id = 0
            self.all_evaluated_params = []
            self.all_run_ids = []

        # Get best performing params for each eval metric
        if not self.no_results_logging:
            self.best_per_metric = self.get_best_performances(self.eval_metrics)

    def get_best_performances(self, eval_metrics):
        """ Get best performing hyperparam configuration up to current iter """
        # Loop over all iterations and get best score for each metric
        best_performances = {}
        for metric in eval_metrics:
            all_scores = []
            if len(self.opt_log.items()) > 0:
                for iter_id, iter_values in self.opt_log.items():
                    all_scores.append(iter_values[metric])
                if self.max_objective:
                    best_id = np.argmax(all_scores) + 1
                else:
                    best_id = np.argmin(all_scores) + 1
                best_score = self.opt_log[best_id][metric]
                best_params = self.opt_log[best_id]["params"]
                best_performances[metric] = {"run_id": best_id,
                                             "score": best_score,
                                             "params": best_params}
            else:
                best_performances[metric] = {"run_id": 0,
                                             "score": 0,
                                             "params": None}
        return best_performances

    def __len__(self):
        return len(self.opt_log)


def evaluate_hyperparams(eval_logs, run_ids, problem_type, eval_metrics):
    """ Run the search for a number of iterations """
    if problem_type == "final":
        # Get final training loss as performance score
        perf_scores = evaluate_final_score(eval_logs,
                                           measure_keys=eval_metrics,
                                           run_ids=run_ids)
    elif problem_type == "best":
        # Get final training loss as performance score
        perf_scores = evaluate_best_score(eval_logs,
                                          measure_keys=eval_metrics,
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
                    eval_logs[run]["stats"][metric]["mean"])
            else:
                int_out[run] = np.min(
                    eval_logs[run]["stats"][metric]["mean"])
        perf_per_metric[metric] = int_out
    return perf_per_metric
