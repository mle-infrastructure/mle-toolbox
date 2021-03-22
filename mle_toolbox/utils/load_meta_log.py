import numpy as np
import h5py
from dotmap import DotMap
from typing import Union, List


def load_meta_log(log_fname: str, mean_seeds: bool=True) -> DotMap:
    """ Load in logging results & mean the results over different runs """
    # Open File & Get array names to load in
    h5f = h5py.File(log_fname, mode="r")
    # Get all ids of all runs (b_1_eval_0_seed_0)
    run_names = list(h5f.keys())
    # Get only stem of ids (b_1_eval_0)
    run_ids = list(set([r_n.split("_seed")[0] for r_n in run_names]))
    # Get all main data source keys ("meta", "stats", "time")
    data_sources = list(h5f[run_names[0]].keys())
    # Get all variables within the data sources
    data_items = {data_sources[i]:
                  list(h5f[run_names[0]][data_sources[i]].keys())
                  for i in range(len(data_sources))}

    # Create a group for each runs (eval and seed)
    # Out: {'b_1_eval_0_seed_0': {'meta': {}, 'stats': {}, 'time': {}}, ...}
    result_dict = {key: {} for key in run_names}
    for rn in run_names:
        run = h5f[rn]
        source_to_store = {key: {} for key in data_sources}
        for ds in data_sources:
            run_source = run[ds]
            data_to_store = {key: {} for key in data_items[ds]}
            for i, o_name in enumerate(data_items[ds]):
                data_to_store[o_name] = run[ds][o_name][:]
            source_to_store[ds] = data_to_store
        result_dict[rn] = source_to_store
    h5f.close()

    # Return as dot-callable dictionary
    if mean_seeds:
        result_dict = mean_over_seeds(result_dict)
    return DotMap(result_dict, _dynamic=False)


def mean_over_seeds(result_dict: DotMap) -> DotMap:
    """ Mean all individual runs over their respective seeds.
        IN: {'b_1_eval_0_seed_0': {'meta': {}, 'stats': {}, 'time': {}},
             'b_1_eval_0_seed_1': {'meta': {}, 'stats': {}, 'time': {}},
              ...}
        OUT: {'b_1_eval_0': {'meta': {}, 'stats': {}, 'time': {},
              'b_1_eval_1': {'meta': {}, 'stats': {}, 'time': {}}
    """
    all_runs = list(result_dict.keys())
    eval_runs = []
    split_by = "_seed_"

    # Get again the different unique runs (without their seeds)
    for run in all_runs:
        split = run.split(split_by)
        eval_runs.append(split[0])
    unique_evals = list(set(eval_runs))

    # Get seeds specific to each one of eval/run - append later on to meta data
    evals_and_seeds = {key: [] for key in unique_evals}
    for run in all_runs:
        split = run.split(split_by)
        evals_and_seeds[split[0]].append(int(split[1]))

    # Loop over all evals (e.g. b_1_eval_0) and merge + aggregate data
    new_results_dict = {}
    for eval in unique_evals:
        all_seeds_for_run = [i for i in all_runs if i.startswith(eval + "_")]
        data_temp = result_dict[all_seeds_for_run[0]]
        # Get all main data source keys ("meta", "stats", "time")
        data_sources = list(data_temp.keys())
        # Get all variables within the data sources
        data_items = {data_sources[i]:
                      list(data_temp[data_sources[i]].keys())
                      for i in range(len(data_sources))}

        # Collect all runs together - data at this point is not modified
        source_to_store = {key: {} for key in data_sources}
        for ds in data_sources:
            data_to_store = {key: [] for key in data_items[ds]}
            for i, o_name in enumerate(data_items[ds]):
                for i, seed_id in enumerate(all_seeds_for_run):
                    seed_run = result_dict[seed_id]
                    data_to_store[o_name].append(seed_run[ds][o_name][:])
            source_to_store[ds] = data_to_store
        new_results_dict[eval] = source_to_store

        # Aggregate over the collected runs
        mean_sources = {key: {} for key in data_sources}
        for ds in data_sources:
            # Mean over time and stats data
            if ds in ["time", "stats"]:
                mean_dict = {key: {} for key in data_items[ds]}
                for i, o_name in enumerate(data_items[ds]):
                    mean_tol, std_tol = tolerant_mean(new_results_dict[eval][ds][o_name])
                    mean_dict[o_name]["mean"] = mean_tol
                    mean_dict[o_name]["std"] = std_tol
            # Append over all meta data (strings, seeds nothing to mean)
            elif ds == "meta":
                mean_dict = {}
                for i, o_name in enumerate(data_items[ds]):
                    temp = np.array(
                    new_results_dict[eval][ds][o_name]).squeeze().astype('U200')
                    # Get rid of duplicate experiment dir strings
                    if o_name in ["experiment_dir", "eval_id", "config_fname",
                                  "model_type"]:
                        mean_dict[o_name] = str(np.unique(temp)[0])
                    else:
                        mean_dict[o_name] = temp

                # Add seeds as clean array of integers to dict
                mean_dict["seeds"] = {}
                mean_dict["seeds"] = evals_and_seeds[eval]
            else:
                raise ValueError
            mean_sources[ds] = mean_dict
        new_results_dict[eval] = mean_sources
    return DotMap(new_results_dict, _dynamic=False)


def tolerant_mean(arrs: list):
    """ Helper function for case where data to mean has different lengths. """
    lens = [len(i) for i in arrs]
    arr = np.ma.empty((np.max(lens),len(arrs)))
    arr.mask = True
    for idx, l in enumerate(arrs):
        arr[:len(l),idx] = l
    return arr.mean(axis = -1), arr.std(axis=-1)


def subselect_meta_log(meta_log: DotMap, run_ids: List[str]):
    """ Subselect the meta log dict based on a list of run ids. """
    sub_log = DotMap()
    for run_id in run_ids:
        sub_log[run_id] = meta_log[run_id]
    return sub_log
