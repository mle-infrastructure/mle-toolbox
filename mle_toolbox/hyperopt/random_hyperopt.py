import numpy as np
from .base_hyperopt import BaseHyperOptimisation
from .hyperopt_logger import HyperoptLogger
from .gen_hyperspace import construct_hyperparam_range


class RandomHyperoptimisation(BaseHyperOptimisation):
    def __init__(self,
                 hyper_log: HyperoptLogger,
                 job_arguments: dict,
                 config_fname: str,
                 job_fname: str,
                 experiment_dir: str,
                 params_to_search: dict,
                 problem_type: str,
                 eval_score_type: str):
        BaseHyperOptimisation.__init__(self, hyper_log, job_arguments,
                                       config_fname, job_fname,
                                       experiment_dir, params_to_search,
                                       problem_type, eval_score_type)
        self.search_type = "random"
        self.param_range = construct_hyperparam_range(self.params_to_search,
                                                      self.search_type)
        self.num_param_configs = len(self.param_range)
        self.eval_counter = len(hyper_log)

    def get_hyperparam_proposal(self, num_iter_per_batch: int):
        """ Get proposals to eval next (in batches) - Random Sampling. """
        param_batch = []
        # Sample a new configuration for each eval in the batch
        while (len(param_batch) < num_iter_per_batch
               and self.eval_counter < self.num_param_configs):
            proposal_params = {}
            # Sample the parameters individually at random from the ranges
            for p_name, p_range in self.param_range.items():
                proposal_params[p_name] = np.random.choice(p_range)
            if not proposal_params in self.hyper_log.all_evaluated_params:
                # Add parameter proposal to the batch list
                param_batch.append(proposal_params)
                self.eval_counter += 1
            else:
                # Otherwise continue sampling proposals
                continue
        return param_batch
