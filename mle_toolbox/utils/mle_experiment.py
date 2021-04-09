from .core import get_configs_ready, set_random_seeds
from .mle_logger import MLE_Logger


class MLE_Experiment(object):
    def __init__(self,
                 config_fname: str="configs/base_config.json",
                 auto_setup: bool=True):
        ''' Load the job configs for the MLE experiment. '''
        # Load the different configurations for the experiment.
        train_config, net_config, log_config = get_configs_ready(config_fname)
        self.train_config = train_config
        self.net_config = net_config
        self.log_config = log_config

        # Make initial setup optional so that configs can be modified ad-hoc
        if auto_setup:
            self.setup()

    def setup(self):
        ''' Set the random seed & initialize the logger. '''
        # Set the random seeds for all random number generation
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
