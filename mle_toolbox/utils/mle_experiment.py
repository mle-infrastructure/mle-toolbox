from typing import Union, List
from .core_experiment import (get_configs_ready,
                              get_extra_cmd_line_input,
                              set_random_seeds)
from .mle_logger import MLE_Logger
from .helpers import print_framed


class MLExperiment(object):
    def __init__(self,
                 config_fname: str="configs/base_config.json",
                 auto_setup: bool=True,
                 create_jax_prng: bool=False,
                 default_seed: int=0):
        ''' Load the job configs for the MLE experiment. '''
        # Load the different configurations for the experiment.
        train_config, net_config, log_config, extra_args = get_configs_ready(
                                                                config_fname)
        # Optional addition of more command line inputs
        extra_config = get_extra_cmd_line_input(extra_args)

        # Add experiment configuration to experiment instance
        self.train_config = train_config
        self.net_config = net_config
        self.log_config = log_config
        self.extra_config = extra_config
        self.create_jax_prng = create_jax_prng
        self.default_seed = default_seed

        # Make initial setup optional so that configs can be modified ad-hoc
        if auto_setup:
            self.setup()

    def setup(self):
        ''' Set the random seed & initialize the logger. '''
        # If no seed is provided in train_config - set it to default
        if "seed_id" not in self.train_config.keys():
            self.train_config.seed_id = self.default_seed
            print_framed(f"!!!WARNING!!!: No seed provided - set to default "
                         f"{self.default_seed}.")

        # Set the random seeds for all random number generation
        if self.create_jax_prng:
            # Return JAX random number generating key
            self.rng = set_random_seeds(self.train_config.seed_id,
                                        return_key=True)
        else:
            set_random_seeds(self.train_config.seed_id)

        # Initialize the logger for the experiment
        self.log = MLE_Logger(**self.log_config)

    def update_log(self,
                   clock_tick: list,
                   stats_tick: list,
                   model=None,
                   plot_to_tboard=None,
                   save=False):
        ''' Update the MLE_Logger instance with stats, model params & save. '''
        self.log.update_log(clock_tick, stats_tick, model,
                            plot_to_tboard, save)
