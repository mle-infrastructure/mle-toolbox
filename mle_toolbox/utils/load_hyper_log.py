import pandas as pd
import numpy as np
from typing import Union, List
from .general import load_pkl_object


def reload_hyper_log(hyper_log_fpath: str):
    """ Reload the previously stored .pkl log file """
    opt_log = load_pkl_object(hyper_log_fpath)
    all_evaluated_params = []
    for key, eval_iter in opt_log.items():
        all_evaluated_params.append(eval_iter["params"])
    return opt_log


def hyper_log_to_df(hyper_log_fpath: str):
    """ Load & transform the dictionary log into a pandas df"""
    # Load the log from the pkl file
    hyper_log = reload_hyper_log(hyper_log_fpath)

    hyper_list = []
    list_of_run_dicts = [hyper_log[i] for i in hyper_log.keys()]

    def merge_two_dicts(x: dict, y: dict):
        """Given two dicts, merge them into new dict as shallow copy."""
        z = x.copy()
        z.update(y)
        return z

    for i in range(len(list_of_run_dicts)):
        # Unpack the individual params dictionaries for better indexing
        unravel_params = merge_two_dicts(list_of_run_dicts[i]["params"], list_of_run_dicts[i])
        del unravel_params["params"]
        hyper_list.append(unravel_params)

    # Put list of dicts into pandas df
    hyper_df = pd.DataFrame(hyper_list)
    return hyper_df


def get_closest_sub_df(df: pd.core.frame.DataFrame,
                       param_name: Union[List[str], str],
                       param_value: Union[List[float], int, float]):
    """ Return df with fixed params closest to param_value in df. """
    # Make sure to iterate over list of parameters + copy the df
    if type(param_name) != list:
        param_name = [param_name]
    if type(param_value) != list:
        param_value = [param_value]
    sub_df = df.copy()

    # Loop over parameters and construct the sub-df
    for i, name in enumerate(param_name):
        all_values = df[name].unique()
        min_id = np.argmin(np.abs(all_values - param_value[i]))
        sub_df = sub_df[sub_df[name] == all_values[min_id]]
    return sub_df
