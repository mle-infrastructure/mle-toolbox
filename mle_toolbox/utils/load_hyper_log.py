import pickle
import pandas as pd
import numpy as np
from typing import Union, List


class HyperLog(object):
    """ Class wrapper for hyper_log dataframe w. additional functionality. """
    def __init__(self, hyper_df: pd.DataFrame):
        self.hyper_log = hyper_df

    def filter(self,
               param_name: Union[None, List[str], str]=None,
               param_value: Union[None, List[float], float]=None,
               metric_name: Union[None, str]=None,
               top_k: int=5,
               maximize_metric: bool=False):
        """ Function to filter runs stored in hyper log:
            1. Fix variables to specific values (closest).
            2. Subselect top k performing runs according to a metric.
        """
        # Filter df: All runs with fixed params closest to param_value
        if param_name is not None:
            df = sub_variable_hyper_log(self.hyper_log, param_name,
                                        param_value)
        # Filter df: Top-k performing runs for metric
        if metric_name is not None:
            df = sub_top_k_hyper_log(self.hyper_log, metric_name, top_k,
                                     maximize_metric)
        return HyperLog(df)

    @property
    def eval_ids(self):
        """ Get ids of runs stored in hyper_log instance. """
        return self.hyper_log.run_id.tolist()

    def __str__(self):
        """ Print the hyper_log. """
        return self.hyper_log

    def __len__(self):
        """ Return number of runs stored in hyper_log. """
        return len(self.eval_ids)


def load_hyper_log(hyper_log_fpath: str):
    """ Load & transform the dictionary log into a pandas df"""
    # Load the log from the pkl file
    hyper_log = load_pkl_hyper_log(hyper_log_fpath)
    # Unravel the subdict of parameters for each iteration
    hyper_list = unravel_param_subdicts(hyper_log)
    # Put list of dicts into pandas df
    hyper_df = pd.DataFrame(hyper_list)
    return HyperLog(hyper_df)


def load_pkl_hyper_log(hyper_log_fpath: str):
    """ Load stored .pkl serach log file as list of iteration dicts. """
    with open(hyper_log_fpath, 'rb') as input:
        opt_log = pickle.load(input)
    all_evaluated_params = []
    # Loop over individual jobs stored in the hyper log
    for key, eval_iter in opt_log.items():
        all_evaluated_params.append(eval_iter["params"])
    return opt_log


def unravel_param_subdicts(hyper_log: list):
    """ Each iteration dict has a subdict summarizing evaluated hyperparams.
        Unpack these so that we can better index individual runs later on. """
    hyper_list = []
    list_of_run_dicts = [hyper_log[i] for i in hyper_log.keys()]

    def merge_two_dicts(x: dict, y: dict):
        """Given two dicts, merge them into new dict as shallow copy. """
        z = x.copy()
        z.update(y)
        return z

    # Unpack the individual params dictionaries for better indexing
    for i in range(len(list_of_run_dicts)):
        unravel_params = merge_two_dicts(list_of_run_dicts[i]["params"],
                                         list_of_run_dicts[i])
        del unravel_params["params"]
        hyper_list.append(unravel_params)
    return hyper_list


def sub_variable_hyper_log(df: pd.core.frame.DataFrame,
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


def sub_top_k_hyper_log(df: pd.core.frame.DataFrame,
                        metric_name: str,
                        top_k: int=5,
                        maximize_metric: bool=False):
    """ Return df with top-k runs sorted ascend/descend for metric. """
    sorted_df = df.sort_values(by=metric_name, ascending=not maximize_metric)
    return sorted_df.head(top_k)
