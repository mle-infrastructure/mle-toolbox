from ..utils import save_pkl_object
import math
import pandas as pd


class PBT_Logger(object):
    def __init__(self, pbt_log_fname: str):
        """ Logging Class for PBT (Jaderberg et al. 17). """
        self.pbt_log_fname = pbt_log_fname
        self.pbt_log = []

    def update_log(self, update_log: dict, save: bool=True):
        """ Update the trace/log of the PBT. """
        self.pbt_log.append(update_log)
        if save:
            self.save_log()

    def save_log(self):
        """ Save the trace/log of the PBT. """
        pbt_df = pd.DataFrame(self.pbt_log).drop_duplicates(
                                              subset=["worker_id",
                                                      "pbt_step_id",
                                                      "num_updates"])
        save_pkl_object(pbt_df, self.pbt_log_fname)


class Population_Logger(object):
    def __init__(self,
                 eval_metric: str,
                 max_objective: bool,
                 num_population_members: int):
        """ Logging class for a running population. """
        self.eval_metric = eval_metric
        self.max_objective = max_objective
        self.num_population_members = num_population_members

    def update_log(self, worker_logs: list):
        """ Store the results of the most recent generation. """
        self.recent_log = pd.DataFrame(worker_logs)

    def get_worker_data(self, worker_id: int):
        """ Select the number of updates & performance for selected worker. """
        worker_data = self.recent_log[self.recent_log.worker_id == worker_id]
        num_updates = worker_data.num_updates.values[0]
        performance = worker_data[self.eval_metric].values[0]
        return num_updates, performance

    def get_top_and_bottom(self, truncation_percent):
        """ Get top and bottom of performance distribution. """
        n_rows = math.ceil(self.num_population_members * truncation_percent)
        if self.max_objective:
            top_df = self.recent_log.nlargest(n_rows, self.eval_metric)
            bottom_df = self.recent_log.nsmallest(n_rows, self.eval_metric)
        else:
            top_df = self.recent_log.nsmallest(n_rows, self.eval_metric)
            bottom_df = self.recent_log.nlargest(n_rows, self.eval_metric)
        return top_df, bottom_df
