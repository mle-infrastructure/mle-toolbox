from typing import Union
from .hyperopt_base import BaseHyperOptimisation
from .hyper_logger import HyperoptLogger
from mle_hyperopt import GridSearch


class GridHyperoptimisation(BaseHyperOptimisation):
    def __init__(
        self,
        hyper_log: HyperoptLogger,
        resource_to_run: str,
        job_arguments: dict,
        config_fname: str,
        job_fname: str,
        experiment_dir: str,
        search_params: dict,
        search_type: str = "grid",
        search_schedule: str = "sync",
        message_id: Union[str, None] = None,
    ):
        BaseHyperOptimisation.__init__(
            self,
            hyper_log,
            resource_to_run,
            job_arguments,
            config_fname,
            job_fname,
            experiment_dir,
            search_params,
            search_type,
            search_schedule,
            message_id,
        )
        # Generate all possible combinations of param configs in list & loop
        # over the list when doing the grid search
        self.strategy = GridSearch(**search_params)
