import argparse
import torch
import gym

from drl_toolbox.utils import set_random_seeds
from drl_toolbox.dl import BodyBuilder, set_optimizer
from drl_toolbox.single_rl import make_parallel_env, ActorCriticBuilder
from drl_toolbox.single_rl.agents import PPO_Agent

from mle_toolbox.utils import DeepLogger, get_configs_ready


def main(train_config, net_config, log_config):
    """ Train & evaluate a policy gradient agent. """
    # Set the training device & the random seed for the example run
    device_name = train_config.device_name
    device = torch.device(device_name)
    set_random_seeds(seed_id=train_config.seed_id, verbose=False)

    # Initialize - Envs, Nets, Optimizer, Train Config, Logger
    train_log = DeepLogger(**log_config)

    train_env = make_parallel_env(train_config.env_name,
                                  train_config.seed_id,
                                  train_config.num_threads)

    test_env = make_parallel_env(train_config.env_name,
                                 train_config.seed_id,
                                 train_config.num_test_episodes)

    # Define two separate networks for actor & critic
    ac_network = ActorCriticBuilder(train_config.policy_type,
                                    net_config["policy"],
                                    net_config["value"],
                                    shared_torso=0,
                                    recurrent_policy=train_config.recurrent_policy,
                                    device=device).to(device)

    # Define the required optimizers
    optimizer = set_optimizer(network=ac_network,
                              opt_type=train_config.opt_type,
                              l_rate=train_config.l_rate)

    # Instantiate PPO agent class with both the actor & critic networks
    pg_agent = PPO_Agent(train_env, test_env, train_config, train_log,
                         ac_network, optimizer, device)


    # Run the training loop for the Policy Gradient agent
    pg_agent.run_learning_loop(train_config.num_env_steps)
    return train_log


if __name__ == "__main__":
    train_config, net_config, log_config = get_configs_ready(
                        default_seed=0,
                        default_config_fname="base_ppo_config.json",
                        default_experiment_dir="experiments/")

    main(train_config, net_config, log_config)
