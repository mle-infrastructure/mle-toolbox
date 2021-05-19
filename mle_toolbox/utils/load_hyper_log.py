import pickle
import pandas as pd
import numpy as np
from typing import Union, List


# Set pandas printing option (print more columns!)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)


class HyperLog(object):
    """ Class wrapper for hyper_log dataframe w. additional functionality. """
    def __init__(self, hyper_df: pd.DataFrame):
        self.hyper_log = hyper_df
        for col in hyper_df.columns:
            setattr(self, col, hyper_df[col])

    def set_search_metrics(self, meta_vars: list, stats_vars: list,
                           time_vars: list):
        """ Reconstruct search & metric variable names from meta log data. """
        self.search_vars = list(set(self.columns) -  set(meta_vars + stats_vars
                                + time_vars + ["run_id", "log_fname"]))
        self.search_metrics = stats_vars

    def filter(self, param_dict: Union[None, dict]=None,
               metric_name: Union[None, str]=None,
               top_k: int=5,
               maximize_metric: bool=False):
        """ Function to filter runs stored in hyper log:
            1. Fix variables to specific values (closest).
            2. Subselect top k performing runs according to a metric.
        """
        # Filter df: All runs with fixed params closest to param_value
        if param_dict is not None:
            df = sub_variable_hyper_log(self.hyper_log,
                                        list(param_dict.keys()),
                                        list(param_dict.values()))
        # Filter df: Top-k performing runs for metric
        if metric_name is not None:
            df = sub_top_k_hyper_log(self.hyper_log, metric_name, top_k,
                                     maximize_metric)

        # Recursively wrap sub df and transfr search vars & metrics
        sub_df = HyperLog(df)
        if 'search_vars' in dir(self):
            sub_df.search_vars = self.search_vars
            sub_df.search_metrics = self.search_metrics
        return sub_df

    def plot_1D_bar(self, var_name:str, metric_name: str,
                    fixed_params: Union[dict, None]=None,
                    fig=None, ax=None):
        """ Plot a 1D bar of metric for filtered hyper_df with 1 dof. """
        from mle_toolbox.visualize import visualize_1D_bar
        visualize_1D_bar(self.hyper_log,
                         param_to_plot=var_name,
                         target_to_plot=metric_name,
                         fixed_params=fixed_params,
                         plot_title=metric_name,
                         xy_labels=[var_name, metric_name],
                         every_nth_tick=1,
                         round_ticks=2,
                         fig=fig, ax=ax)

    def plot_2D_heat(self, var_names: List[str], metric_name: str,
                     fixed_params: Union[dict, None]=None,
                     fig=None, ax=None):
        """ Plot a 2D heat of metric for filtered hyper_df with 2 dof. """
        from mle_toolbox.visualize import visualize_2D_grid
        visualize_2D_grid(self.hyper_log,
                          params_to_plot=var_names,
                          target_to_plot=metric_name,
                          fixed_params=fixed_params,
                          plot_title=metric_name,
                          plot_subtitle=fixed_params,
                          xy_labels=var_names,
                          variable_name=metric_name,
                          round_ticks=2,
                          text_in_cell=False,
                          fig=fig, ax=ax)

    def unique(self, var_name: Union[str, None, List[str]]=None):
        """ Get unique values of (all) variable. """
        # Get unique values for single column
        if type(var_name) == str:
            return self.hyper_log[var_name].unique()
        # Get unique values for list of columns
        elif type(var_name) == list:
            for v in var_name:
                unique_dict[v] = self.hyper_log[v].unique()
            return unique_dict
        # Get unique values for all columns
        elif var_name is None:
            unique_dict = {}
            for v in self.columns:
                try:
                    unique_dict[v] = self.hyper_log[v].unique()
                except:
                    pass
            return unique_dict

    @property
    def columns(self):
        """ Get columns of hyper_log dataframe. """
        return list(self.hyper_log.columns)

    @property
    def eval_ids(self):
        """ Get ids of runs stored in hyper_log instance. """
        return self.hyper_log.run_id.tolist()

    def __str__(self):
        """ Print the hyper_log. """
        return str(self.hyper_log)

    def __repr__(self):
        """ Represent the hyper_log. """
        return str(self.hyper_log)

    def __len__(self):
        """ Return number of runs stored in hyper_log. """
        return len(self.eval_ids)

    def __getitem__(self, item):
        """ Get run log via string subscription. """
        return self.hyper_log[item]


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
        if type(param_value[i]) == float or type(param_value[i]) == int:
            all_values = all_values.astype(float)
            min_id = np.argmin(np.abs(all_values - float(param_value[i])))
            sub_df = sub_df[sub_df[name].astype(float) == all_values[min_id]]
        elif type(param_value[i]) == str:
            sub_df = sub_df[sub_df[name] == param_value[i]]
        else:
            raise ValueError("Please provide a int/float/str value to filter.")
    return sub_df


def sub_top_k_hyper_log(df: pd.core.frame.DataFrame,
                        metric_name: str,
                        top_k: int=5,
                        maximize_metric: bool=False):
    """ Return df with top-k runs sorted ascend/descend for metric. """
    sorted_df = df.sort_values(by=metric_name, ascending=not maximize_metric)
    return sorted_df.head(top_k)
