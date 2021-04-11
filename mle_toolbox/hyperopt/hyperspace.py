import numpy as np
from skopt.space import Real, Integer, Categorical


def construct_hyperparam_range(params_to_search: dict,
                               search_type: str) -> dict:
    """ Helper to generate list of hyperparam ranges from YAML dictionary. """
    param_range = {}
    # For random/grid hyperopt simply generate numpy lists with resolution
    if search_type in ["random", "grid"]:
        if "categorical" in params_to_search.keys():
            for k, v in params_to_search["categorical"].items():
                param_range[k] = v
        if "real" in params_to_search.keys():
            for k, v in params_to_search["real"].items():
                param_range[k] = np.linspace(float(v["begin"]), float(v["end"]),
                                             int(v["bins"])).tolist()
        if "integer" in params_to_search.keys():
            for k, v in params_to_search["integer"].items():
                param_range[k] = np.arange(int(v["begin"]), int(v["end"]),
                                           int(v["spacing"])).tolist()
    # For SMBO-based hyperopt generate spaces with skopt classes
    elif search_type == "smbo":
        # Can specify prior distribution over hyperp. distrib
        # log-uniform samples more from the lower tail of the hyperparam range
        #   real: ["uniform", "log-uniform"]
        #   integer: ["uniform", "log-uniform"]
        if "categorical" in params_to_search.keys():
            for k, v in params_to_search["categorical"].items():
                param_range[k] = Categorical(v, name=k)
        if "real" in params_to_search.keys():
            for k, v in params_to_search["real"].items():
                param_range[k] = Real(float(v["begin"]), float(v["end"]),
                                      prior=v["prior"], name=k)
        if "integer" in params_to_search.keys():
                param_range[k] = Integer(int(v["begin"]), int(v["end"]),
                                         prior=v["prior"], name=k)
    else:
        raise ValueError("Please provide a valid hyperparam search type.")
    return param_range
