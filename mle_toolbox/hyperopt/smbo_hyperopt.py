import numpy as np
from .base_hyperopt import BaseHyperOptimisation
from .hyperopt_logger import HyperoptLogger
from .gen_hyperspace import construct_hyperparam_range


class SMBOHyperoptimisation(BaseHyperOptimisation):
    def __init__(self,
                 hyper_log: HyperoptLogger,
                 job_arguments: dict,
                 config_fname: str,
                 job_fname: str,
                 experiment_dir: str,
                 params_to_search: dict,
                 problem_type: str,
                 eval_score_type: str,
                 smbo_config: dict):
        try:
            from skopt import Optimizer
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError(f"{err}. You need to install `scikit-optimize` "
                                      "to use the `mle_toolbox.hyperopt` module.")

        BaseHyperOptimisation.__init__(self, hyper_log, job_arguments,
                                       config_fname, job_fname,
                                       experiment_dir, params_to_search,
                                       problem_type, eval_score_type)
        self.search_type = "smbo"
        self.param_range = construct_hyperparam_range(self.params_to_search,
                                                      self.search_type)

        # Initialize the surrogate model/hyperparam config proposer
        self.hyper_optimizer = Optimizer(dimensions=list(self.param_range.values()),
                                random_state=1,
                                base_estimator=smbo_config["base_estimator"],
                                acq_func=smbo_config["acq_function"],
                                n_initial_points=smbo_config["n_initial_points"])

    def get_hyperparam_proposal(self, num_iter_per_batch: int):
        """ Get proposals to eval next (in batches) - Random Sampling. """
        param_batch = []
        proposals = self.hyper_optimizer.ask(n_points=num_iter_per_batch)
        # Generate list of dictionaries with different hyperparams to evaluate
        for prop in proposals:
            proposal_params = {}
            for i, p_name in enumerate(self.param_range.keys()):
                proposal_params[p_name] = prop[i]
            param_batch.append(proposal_params)
        return param_batch

    def clean_up_after_batch_iteration(self, batch_proposals, perf_measures):
        """ Perform post-iteration clean-up by updating surrogate model. """
        x, y = [], []
        # First key of all metrics is used to update the surrogate!
        to_model = perf_measures.keys()[0]
        # TODO: Do multi-objective SMBO?!
        for i, prop in enumerate(batch_proposals):
            x.append(list(prop.values()))
            # skopt assumes we want to minimize surrogate model
            # Make performance negative if we maximize
            effective_perf = (-1*perf_measures[to_model][i] if self.hyper_log.max_target
                              else perf_measures[to_model][i])
            y.append(effective_perf)
        self.hyper_optimizer.tell(x, y)
