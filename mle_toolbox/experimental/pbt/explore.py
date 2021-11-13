import numpy as np


class ExplorationStrategy(object):
    def __init__(self, strategy: str, pbt_params: dict):
        """Exploration Strategies for PBT (Jaderberg et al. 17)."""
        assert strategy in ["perturb", "resample", "additive-noise"]
        self.strategy = strategy
        self.pbt_params = pbt_params
        self.variable_types = list(self.pbt_params.keys())

    def perturb(self, hyperparams: dict) -> dict:
        """Multiply hyperparam independently by random factor of 0.8/1.2."""
        new_hyperparams = {}
        for param_name, param_value in hyperparams.items():
            new_hyperparams[param_name] = np.random.choice([0.8, 1.2]) * param_value
        return new_hyperparams

    def resample(self) -> dict:
        """Resample hyperparam from original prior distribution."""
        # TODO: Allow various prior distributions (uniform, log-uniform, etc.)
        hyperparams = {}
        # Loop over categorical, real and integer-valued vars and sample
        for var_type in self.variable_types:
            for param_name in self.pbt_params[var_type]:
                param_dict = self.pbt_params[var_type][param_name]
                param_value = sample_hyperparam(var_type, param_name, param_dict)
                hyperparams[param_name] = param_value
        return hyperparams

    def noisify(self, hyperparams: dict, noise_scale: float = 0.2) -> dict:
        """Add independent Gaussian noise to all float hyperparams."""
        # Uses scale of 0.2 as in example notebook
        # https://github.com/bkj/pbt/blob/master/pbt.ipynb
        new_hyperparams = {}
        for param_name, param_value in hyperparams.items():
            # Sample gaussian noise and add it to the parameter
            eps = np.random.normal() * noise_scale
            new_hyperparams[param_name] = param_value + eps
        return new_hyperparams

    def explore(self, hyperparams: dict) -> dict:
        """Perform an exploration step."""
        if self.strategy == "perturb":
            hyperparams = self.perturb(hyperparams)
        elif self.strategy == "resample":
            hyperparams = self.resample()
        elif self.strategy == "additive-noise":
            hyperparams = self.noisify(hyperparams)
        return hyperparams

    def init_hyperparams(self, worker_id: int) -> dict:
        """Allow user to specify initial hyperparams per worker."""
        hyperparams = {}
        # Loop over categorical, real and integer-valued vars and sample
        for var_type in self.variable_types:
            for param_name in self.pbt_params[var_type]:
                param_dict = self.pbt_params[var_type][param_name]
                # If init in param dict - take init value otherwise sample
                if "init" in param_dict.keys():
                    param_value = param_dict["init"][worker_id]
                else:
                    param_value = sample_hyperparam(var_type, param_name, param_dict)
                hyperparams[param_name] = param_value
        return hyperparams


def sample_hyperparam(var_type: str, param_name: str, param_dict: dict):
    """Sample a hyperparameter from range/discrete set."""
    if var_type == "real":
        param_value = np.random.uniform(float(param_dict.begin), float(param_dict.end))
    elif var_type == "categorical":
        param_value = np.random.choice(param_dict)
    elif var_type == "integer":
        param_range = np.arange(int(param_dict.begin), int(param_dict.end)).tolist()
        param_value = np.random.choice(param_range)
    return param_value
