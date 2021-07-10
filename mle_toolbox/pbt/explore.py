import numpy as np


class ExplorationStrategy(object):
    def __init__(self, strategy: str, pbt_params: dict):
        """ Exploration Strategies for PBT (Jaderberg et al. 17). """
        assert strategy in ["perturb", "resample"]
        self.strategy = strategy
        self.pbt_params = pbt_params
        self.variable_types = list(self.pbt_params.keys())

    def perturb(self, hyperparams: dict):
        """ Multiply hyperparam independently by random factor of 0.8/1.2. """
        new_hyperparams = {}
        for param_name, param_value in hyperparams.items():
            new_hyperparams[param_name] = (np.random.choice([0.8, 1.2])
                                           * param_value)   # noqa: W503
        return new_hyperparams

    def resample(self):
        """ Resample hyperparam from original prior distribution. """
        # TODO: Allow various prior distributions (uniform, log-uniform, etc.)
        hyperparams = {}
        # Loop over categorical, real and integer-valued vars and sample
        for var_type in self.variable_types:
            for param_name in self.pbt_params[var_type]:
                param_dict = self.pbt_params[var_type][param_name]
                if var_type == "real":
                    param_value = np.random.uniform(float(param_dict.begin),
                                                    float(param_dict.end))
                elif var_type == "categorical":
                    param_value = np.random.choice(param_dict)
                elif var_type == "integer":
                    param_range = np.arange(int(param_dict.begin),
                                            int(param_dict.end)).tolist()
                    param_value = np.random.choice(param_range)
                hyperparams[param_name] = param_value
        return hyperparams

    def explore(self, hyperparams: dict):
        """ Perform an exploration step. """
        if self.strategy == "perturb":
            hyperparams = self.perturb(hyperparams)
        elif self.strategy == "resample":
            hyperparams = self.resample()
        return hyperparams
