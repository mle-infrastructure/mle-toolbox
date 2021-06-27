from typing import Union, List
from .core_experiment import (load_experiment_config,
                              parse_experiment_args,
                              get_extra_cmd_line_input,
                              set_random_seeds)
from .mle_logger import MLE_Logger
from .load_model import load_model
from .helpers import print_framed


class MLExperiment(object):
    def __init__(self,
                 default_config_fname: str="configs/base_config.json",
                 default_experiment_dir: str="experiments/",
                 default_seed: int=0,
                 auto_setup: bool=True,
                 create_jax_prng: bool=False):
        ''' Load the job configs for the MLE experiment. '''
        # Parse experiment command line arguments
        cmd_args, extra_args = parse_experiment_args(default_config_fname,
                                                     default_seed,
                                                     default_experiment_dir)
        # Load the different configurations for the experiment.
        loaded_configs = load_experiment_config(cmd_args.config_fname,
                                                cmd_args.experiment_dir,
                                                cmd_args.seed_id,
                                                cmd_args.model_ckpt)
        # Optional addition of more command line inputs
        extra_config = get_extra_cmd_line_input(extra_args)

        # Add experiment configuration to experiment instance
        self.train_config = loaded_configs[0]
        self.model_config = loaded_configs[1]
        self.log_config = loaded_configs[2]
        self.extra_config = extra_config
        self.create_jax_prng = create_jax_prng
        self.default_seed = default_seed
        self.model_ckpt = cmd_args.model_ckpt

        # Make initial setup optional so that configs can be modified ad-hoc
        if auto_setup:
            self.setup()

    def setup(self):
        ''' Set the random seed, initialize logger & reload a model. '''
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

        # Load model if checkpoint is provided
        if self.model_ckpt is not None:
            self.model_ckpt = load_model(self.model_ckpt,
                                         self.log_config.model_type)

    def update_log(self,
                   clock_tick: dict,
                   stats_tick: dict,
                   model=None,
                   plot_to_tboard=None,
                   save=False):
        ''' Update the MLE_Logger instance with stats, model params & save. '''
        self.log.update_log(clock_tick, stats_tick, model,
                            plot_to_tboard, save)
