from collections.abc import Mapping, Sequence, Iterable
from functools import partial, reduce
import operator
from itertools import product
import numpy as np
from .base_hyperopt import BaseHyperOptimisation
from .hyperopt_logger import HyperoptLogger
from .gen_hyperspace import construct_hyperparam_range


class GridHyperoptimisation(BaseHyperOptimisation):
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
        # Generate all possible combinations of param configs in list & loop
        # over the list when doing the grid search
        self.search_type = "grid"
        self.param_range = construct_hyperparam_range(self.params_to_search,
                                                      self.search_type)
        self.param_grid = self.generate_search_grid()
        self.num_param_configs = len(self.param_grid)
        self.eval_counter = len(hyper_log)

    def get_hyperparam_proposal(self, num_iter_per_batch: int):
        """ Get proposals to eval next (in batches) - Grid Search """
        param_batch = []
        # Sample a new configuration for each eval in the batch
        while (len(param_batch) < num_iter_per_batch
               and self.eval_counter < self.num_param_configs):
            # Get parameter batch from the grid
            proposal_params = self.param_grid[self.eval_counter]
            if not proposal_params in self.hyper_log.all_evaluated_params:
                # Add parameter proposal to the batch list
                param_batch.append(proposal_params)
                self.eval_counter += 1
            else:
                # Otherwise continue sampling proposals
                continue
        return param_batch

    def generate_search_grid(self):
        """ Construct the parameter grid & return as a list to index """
        return list(ParameterGrid(self.param_range))


class ParameterGrid:
    """ Param Grid Class taken from sklearn: https://tinyurl.com/yj53efc9 """
    def __init__(self, param_grid):
        if not isinstance(param_grid, (Mapping, Iterable)):
            raise TypeError('Parameter grid is not a dict or '
                            'a list ({!r})'.format(param_grid))

        if isinstance(param_grid, Mapping):
            # wrap dictionary in a singleton list to support either dict
            # or list of dicts
            param_grid = [param_grid]

        # check if all entries are dictionaries of lists
        for grid in param_grid:
            if not isinstance(grid, dict):
                raise TypeError('Parameter grid is not a '
                                'dict ({!r})'.format(grid))
            for key in grid:
                if not isinstance(grid[key], Iterable):
                    raise TypeError('Parameter grid value is not iterable '
                                    '(key={!r}, value={!r})'
                                    .format(key, grid[key]))

        self.param_grid = param_grid

    def __iter__(self):
        for p in self.param_grid:
            # Always sort the keys of a dictionary, for reproducibility
            items = sorted(p.items())
            if not items:
                yield {}
            else:
                keys, values = zip(*items)
                for v in product(*values):
                    params = dict(zip(keys, v))
                    yield params

    def __len__(self):
        """Number of points on the grid."""
        # Product function that can handle iterables (np.product can't).
        product = partial(reduce, operator.mul)
        return sum(product(len(v) for v in p.values()) if p else 1
                   for p in self.param_grid)

    def __getitem__(self, ind):
        # This is used to make discrete sampling without replacement memory
        # efficient.
        for sub_grid in self.param_grid:
            # TODO: could memoize information used here
            if not sub_grid:
                if ind == 0:
                    return {}
                else:
                    ind -= 1
                    continue

            # Reverse so most frequent cycling parameter comes first
            keys, values_lists = zip(*sorted(sub_grid.items())[::-1])
            sizes = [len(v_list) for v_list in values_lists]
            total = np.product(sizes)

            if ind >= total:
                # Try the next grid
                ind -= total
            else:
                out = {}
                for key, v_list, n in zip(keys, values_lists, sizes):
                    ind, offset = divmod(ind, n)
                    out[key] = v_list[offset]
                return out

        raise IndexError('ParameterGrid index out of range')
