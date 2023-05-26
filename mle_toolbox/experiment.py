from typing import Union
import functools
from .utils.core_experiment import (
    load_job_config,
    parse_experiment_args,
    get_extra_cmd_line_input,
    set_random_seeds,
    setup_proxy_server,
    mle_config,
)
from .utils.helpers import print_framed, get_os_env_ready
from mle_logging import MLELogger
from mle_logging.load import load_model


class MLExperiment(object):
    def __init__(
        self,
        config_fname: str = "configs/base_config.json",
        experiment_dir: str = "experiments/",
        seed_id: int = 0,
        auto_setup: bool = True,
        create_jax_prng: bool = False,
        train_config: Union[None, dict] = None,
        log_config: Union[None, dict] = None,
        model_config: Union[None, dict] = None,
        device_config: Union[None, dict] = None,
    ):
        """Load job configuration for MLE experiment, setup logger & random seeds."""
        setup_proxy_server()
        self.config_fname = config_fname
        self.experiment_dir = experiment_dir
        # Parse experiment command line arguments
        cmd_args, extra_args = parse_experiment_args(
            config_fname, seed_id, experiment_dir
        )
        # Load the different configurations for the experiment.
        loaded_configs = load_job_config(
            cmd_args.config_fname,
            cmd_args.experiment_dir,
            cmd_args.seed_id,
            cmd_args.model_ckpt_path,
            train_config,
            log_config,
            model_config,
            device_config,
        )
        # Optional addition of more command line inputs
        extra_config = get_extra_cmd_line_input(extra_args)

        # Add experiment configuration to experiment instance
        self.train_config = loaded_configs[0]
        self.model_config = loaded_configs[1]
        self.log_config = loaded_configs[2]
        self.device_config = loaded_configs[3]
        self.extra_config = extra_config
        self.create_jax_prng = create_jax_prng
        self.default_seed = seed_id
        self.seed_id = seed_id

        # Get model ckpt path from command line argument or look in config!
        self.model_ckpt_path = cmd_args.model_ckpt_path
        if self.model_ckpt_path is None:  # Based on mle-hyperopt extra dict
            base_ckpt_names = ["ckpt", "model_ckpt"]
            extra_ckpt_names = ["sh_ckpt", "pbt_ckpt"]
            for m in base_ckpt_names:
                if m in self.train_config.keys():
                    self.model_ckpt_path = self.train_config[m]
            if "extra" in self.train_config.keys():
                for m in extra_ckpt_names:
                    if m in self.train_config.extra.keys():
                        self.model_ckpt_path = self.train_config.extra[m]

        # Get data for W&B from commandline (project, group/sweep)
        self.wb_project = cmd_args.wb_project
        self.wb_group = cmd_args.wb_group
        self.wb_name = cmd_args.wb_name

        # Make initial setup optional so that configs can be modified ad-hoc
        if auto_setup:
            self.setup()
            self.experiment_dir = self.log.experiment_dir

    def setup(self) -> None:
        """Set the random seed, initialize logger & reload a model."""
        # If no seed is provided in train_config - set it to default
        if "seed_id" not in self.train_config.keys():
            self.train_config.seed_id = self.default_seed
            self.log_config.seed_id = self.default_seed
            print_framed(
                "!!!WARNING!!!: No seed provided - set to default "
                f"{self.default_seed}."
            )

        # Setup the device configuration (cuda visibility, jax, etc)
        if self.device_config is not None:
            get_os_env_ready(**self.device_config)

        self.seed_id = self.train_config.seed_id
        # Set the random seeds for all random number generation
        if self.create_jax_prng:
            # Return JAX random number generating key
            self.rng = set_random_seeds(
                self.train_config.seed_id, return_key=True
            )
        else:
            set_random_seeds(self.train_config.seed_id)

        # Initialize the logger for the experiment
        if "use_wandb" in self.log_config.keys():
            if self.log_config.use_wandb:
                # Init empty wandb config dict - if no info provided in config
                if "wandb_config" not in self.log_config.keys():
                    self.log_config["wandb_config"] = {}

                # Add data from mle_config if not otherwise provided
                for k in ["key", "entity"]:
                    if k not in self.log_config.wandb_config.keys():
                        self.log_config.wandb_config[k] = mle_config.wandb[k]

                # Add project/group for W&B logging (if provided)
                if "project" not in self.log_config.wandb_config.keys():
                    if self.wb_project is not None:
                        self.log_config.wandb_config[
                            "project"
                        ] = self.wb_project
                    else:
                        self.log_config.wandb_config["project"] = "prototyping"
                if "group" not in self.log_config.wandb_config.keys():
                    if self.wb_group is not None:
                        self.log_config.wandb_config["group"] = self.wb_group
                    else:
                        self.log_config.wandb_config["group"] = None
                if "name" not in self.log_config.wandb_config.keys():
                    if self.wb_name is not None:
                        self.log_config.wandb_config["name"] = self.wb_name
                    else:
                        self.log_config.wandb_config["group"] = None

        self.log = MLELogger(**self.log_config)

        # Load model if checkpoint is provided
        if self.model_ckpt_path is not None:
            self.model_ckpt = load_model(
                self.model_ckpt_path, self.log_config.model_type
            )
        else:
            self.model_ckpt = None

    def update_log(
        self,
        clock_tick: dict,
        stats_tick: dict,
        model=None,
        plot_fig=None,
        extra_obj=None,
        save=False,
    ) -> None:
        """Update the MLE_Logger instance with stats, model params & save."""
        self.log.update(
            clock_tick, stats_tick, model, plot_fig, extra_obj, save
        )

    def ready_to_log(self, update_counter: int) -> bool:
        """Check whether update_counter is modulo of log_every_k_steps in logger."""
        return self.log.ready_to_log(update_counter)


def experiment(
    config_fname: str = "configs/base_config.json",
    experiment_dir: str = "experiments/",
    seed_id: int = 0,
    auto_setup: bool = True,
    create_jax_prng: bool = False,
    train_config: Union[None, dict] = None,
    log_config: Union[None, dict] = None,
    model_config: Union[None, dict] = None,
):
    """
    Simple experiment decorator. Creates global `mle` experiment instance.
    - If you provide the decorator with a config_fname it will set it as default.
    - The default will be loaded if no other arguments are passed as input.
    This way you can for example also use the `MLExperiment` setup in notebooks.
    Usage:
    @experiment()
    def train(mle):
        '''Train a neural network'''
        for epoch in range(mle.train_config.num_epochs):
            ...
    You can then simply call train() and it will try to load `configs/base_config.json`
    If it doesn't exist the run will print a message & continue with a minimal config.
    You can also directly pass a config_fname and other info to the decorator:
    @experiment(config_fname="your-config-path.yaml")
    def train(mle):
        ...
    """
    mle = MLExperiment(
        config_fname,
        experiment_dir,
        seed_id,
        auto_setup,
        create_jax_prng,
        train_config,
        log_config,
        model_config,
    )

    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            result = function(mle, *args, **kwargs)
            return result

        return wrapper

    return decorator
