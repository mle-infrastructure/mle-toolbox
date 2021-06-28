from ..utils import save_pkl_object
import math
import pandas as pd


class PBT_Logger(object):
    def __init__(self,
                 pbt_log_fname: str,
                 max_objective: bool,
                 eval_metric: str,
                 num_population_members: int,
                 num_total_update_steps: int,
                 num_steps_until_ready: int,
                 num_steps_until_eval: int):
        """ Logging Class for PBT (Jaderberg et al. 17). """
        self.pbt_log_fname = pbt_log_fname
        self.max_objective = max_objective
        self.eval_metric = eval_metric
        self.log_update_counter = 0

        self.num_population_members = num_population_members
        self.num_total_update_steps = num_total_update_steps
        self.num_steps_until_ready = num_steps_until_ready
        self.num_steps_until_eval = num_steps_until_eval

    def update_log(self, worker_logs: list, save: bool=True):
        """ Update the trace/log of the PBT. """
        self.recent_log = pd.DataFrame(worker_logs)
        if self.log_update_counter == 0:
            self.pbt_log = pd.DataFrame(worker_logs)
        else:
            self.pbt_log.append(pd.DataFrame(worker_logs))
        self.pbt_log = self.pbt_log.drop_duplicates(subset=["worker_id",
                                                            "pbt_step_id"])
        self.log_update_counter += 1

        if save:
            self.save_log()

    def save_log(self):
        """ Save the trace/log of the PBT. """
        save_pkl_object(self.pbt_log, self.pbt_log_fname)

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
