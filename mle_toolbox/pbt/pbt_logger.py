from ..utils import save_pkl_object


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

        self.num_population_members = num_population_members
        self.num_total_update_steps = num_total_update_steps
        self.num_steps_until_ready = num_steps_until_ready
        self.num_steps_until_eval = num_steps_until_eval

    def update(self):
        """ Update the trace/log of the PBT. """

    def save_log(self):
        """ Save the trace/log of the PBT. """
        save_pkl_object(self.pbt_log, self.pbt_log_fname)
