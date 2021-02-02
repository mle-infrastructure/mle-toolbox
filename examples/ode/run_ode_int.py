import numpy as np
from mle_toolbox.utils import get_configs_ready, DeepLogger


def main(train_config, net_config, log_config):
    """ Euler integrate a simple ODE for a specified length of time steps. """
    # Instantiate the logger object for the experiment
    log = DeepLogger(**log_config)

    # Define function to integrate & run the integration
    def func(x):
        return -0.1*x

    # Let seed determine initial condition
    x_t = [train_config.x_0 + train_config.seed_id]
    t_seq = np.arange(train_config.dt, train_config.t_max,
                      train_config.dt).tolist()

    for i, t in enumerate(t_seq):
        x_t.append(x_t[-1] + func(x_t[-1])*train_config.dt
                   + (train_config.noise_mean + train_config.noise_std*
                      np.random.normal())*train_config.dt)

        # Update & save the newest log
        if (i % train_config.log_every_steps) == 0:
            time_tick = [i+1]
            stats_tick = [x_t[-1], np.random.normal()]
            log.update_log(time_tick, stats_tick)
            log.save_log()
    return


if __name__ == "__main__":
    # Load in the configuration for the experiment
    configs = get_configs_ready(default_config_fname="ode_int_config_1.json")
    train_config, net_config, log_config = configs
    # Run the simulation/Experiment
    main(train_config, net_config, log_config)
