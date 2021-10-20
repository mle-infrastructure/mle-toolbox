from typing import Union
from .hyperopt_base import BaseHyperOptimisation
from .hyper_logger import HyperoptLogger
from mle_hyperopt import (GridSearch,
                          RandomSearch,
                          SMBOSearch,
                          NevergradSearch,
                          CoordinateSearch)
from mle_toolbox import mle_config


class MLE_Hyperoptimisation(BaseHyperOptimisation):
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
        search_config: Union[None, dict] = None,
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
        if search_type == "grid":
            self.strategy = GridSearch(**search_params,
                                       seed_id=mle_config.general.random_seed)
        elif search_type == "random":
            self.strategy = RandomSearch(**search_params,
                                         search_config=search_config,
                                         seed_id=mle_config.general.random_seed)
        elif search_type == "smbo":
            self.strategy = SMBOSearch(**search_params,
                                       search_config=search_config,
                                       seed_id=mle_config.general.random_seed)
        elif search_type == "nevergrad":
            self.strategy = NevergradSearch(**search_params,
                                            search_config=search_config,
                                            seed_id=mle_config.general.random_seed)
        elif search_type == "coordinate":
            self.strategy = CoordinateSearch(**search_params,
                                             search_config=search_config,
                                             seed_id=mle_config.general.random_seed)

        # Reload data to strategy if applicable
        if self.hyper_log.reloaded:
            self.strategy.load(self.search_log_path)
