import time
import pprint
import numpy as np
import logging
from ..utils.general import load_pkl_object, save_pkl_object


class HyperoptLogger(object):
    def __init__(self, hyperlog_fname: str, max_target: bool=True,
                 verbose: bool=True, reload: bool=False):
        """ Mini-class to log the  """
        self.hyperlog_fname = hyperlog_fname    # Where to save the log to
        self.max_target = max_target  # Whether we want to max target (reward)
        self.verbose = verbose
        if self.max_target: self.best_target = -np.inf
        else: self.best_target = np.inf

        # Instantiate the meta-logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        if reload:
            self.reload_log()
            self.logger.info("Reloaded Log with {} Evaluations".format(self.iter_id))
            self.logger.info("Best evaluation so far: Iter {} | Params {}".format(self.best_iter_id,
                                                                                  self.best_params))
        else:
            self.opt_log = {}               # List of dict of evals
            self.iter_id = 0                # How many iterations already eval
            self.all_run_ids = []           # All run ids of evals
            self.all_evaluated_params = []  # All evaluated parameters
            self.best_iter_id, self.best_params = 0, {}  # Best eval so far

        self.batch_id = 0                   # Batch evaluation tracker

    def update_log(self, params, target, time_elapsed, run_ids):
        """ Update the log dictionary with the most recent result dictionary """
        # Update the batch evaluation counter
        self.batch_id += 1

        # Need to account for batch case - log list of dictionaries!
        if not isinstance(params, list):
            params, target = list(params), list(target)

        # Get best performance in current batch - useful for saving best log/net
        self.best_iter_in_batch = np.argmax(target)

        # Loop over list entries and log them individually
        for iter in range(len(params)):
            self.iter_id += 1
            current_iter = {"params": params[iter],
                            "target": target[iter],
                            "time_elapsed": time_elapsed,
                            "run_id": run_ids[iter]}
            self.opt_log[self.iter_id] = current_iter

            # Store all evaluated parameters!
            self.all_evaluated_params.append(params[iter])

        # Keep track of all results/runs sofar!
        self.all_run_ids += run_ids
        # Update best performance tracker
        iter_id, target, params = self.get_best_performance()

        # Print currently best evaluation
        if self.verbose:
            self.logger.info("BATCH - {} | Total: {} | Best: {:.2f} (Iter {}) | Current: {:.2f}".format(
            self.batch_id, self.iter_id, target, iter_id,
            self.opt_log[self.iter_id]["target"]))
            self.logger.info("BEST PARAMS - {}".format(params))

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
            self.get_best_performance()
        except:
            self.opt_log = {}
            self.iter_id = 0
            self.all_evaluated_params = []
            self.all_run_ids = []
            self.best_iter_id, self.best_params = 0, {}

    def get_best_performance(self):
        """ Get best performing hyperparam configuration up to current iter """
        # Define Boolean to indicate if we found a better param config lately
        self.updated_best_performance = 0

        # In first iteration we have to disregard any baseline & construct 1st
        for iter_id, iter_values in self.opt_log.items():
            if self.max_target and iter_values["target"] > self.best_target:
                self.best_iter_id = iter_id
                self.best_target = iter_values["target"]
                self.best_params = iter_values["params"]
                self.updated_best_performance = 1
            elif not self.max_target and iter_values["target"] < self.best_target:
                self.best_iter_id = iter_id
                self.best_target = iter_values["target"]
                self.best_params = iter_values["params"]
                self.updated_best_performance = 1
        return self.best_iter_id, self.best_target, self.best_params

    def __len__(self):
        return len(self.opt_log)


if __name__ == "__main__":
    hyper_log = HyperoptLogger("hyper_log.pkl")
