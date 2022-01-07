from typing import Union
from .hyperopt_base import BaseHyperOptimisation
from .hyper_logger import HyperoptLogger
from mle_hyperopt import Strategies
from mle_toolbox import mle_config
from mle_monitor import MLEProtocol


class MLE_BatchSearch(BaseHyperOptimisation):
    def __init__(
        self,
        hyper_log: HyperoptLogger,
        resource_to_run: str,
        job_arguments: dict,
        config_fname: str,
        job_fname: str,
        experiment_dir: str,
        search_params: dict,
        search_type: str = "Grid",
        search_schedule: str = "sync",
        search_config: Union[None, dict] = None,
        message_id: Union[str, None] = None,
        protocol_db: Union[MLEProtocol, None] = None,
        debug_mode: bool = False,
    ):
        """Simple wrapper around `mle-hyperopt` strategies."""
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
            protocol_db,
            debug_mode,
        )
        assert search_type in [
            "Grid",
            "Random",
            "SMBO",
            "Coordinate",
            "Nevergrad",
            "PBT",
            "Halving",
            "Hyperband",
        ]
        self.strategy = Strategies[search_type](
            **search_params,
            search_config=search_config,
            maximize_objective=hyper_log.max_objective,
            seed_id=mle_config.general.random_seed,
            verbose=True
        )

        # Reload data to strategy if applicable
        if self.hyper_log.reloaded:
            self.strategy.load(self.search_log_path)
