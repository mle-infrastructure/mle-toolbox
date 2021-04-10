import numpy as np
import matplotlib.pyplot as plt
from mle_toolbox import MLExperiment


def main(mle):
    """ Euler integrate a simple ODE for a specified length of time steps. """
    # Define function to integrate & run the integration
    def func(x):
        return -0.1*x

    # Let seed determine initial condition
    x_t = [mle.train_config.x_0 + mle.train_config.seed_id]
    t_seq = np.arange(mle.train_config.dt,
                      mle.train_config.t_max,
                      mle.train_config.dt).tolist()

    for i, t in enumerate(t_seq):
        x_t.append(x_t[-1] + func(x_t[-1])*mle.train_config.dt
                   + (mle.train_config.noise_mean
                      + mle.train_config.noise_std*
                      np.random.normal()) * mle.train_config.dt)

        # Update & save the newest log
        if (i % mle.train_config.log_every_steps) == 0:
            time_tick = [i+1]
            stats_tick = [x_t[-1], np.random.normal()]
            mle.update_log(time_tick, stats_tick, save=True)

    # Generate a sample plot and store it
    fig = sample_plot()
    mle.log.save_plot(fig, "_sin_curve.png")
    return


def sample_plot():
    # Data for plotting
    t = np.arange(0.0, 2.0, 0.01)
    s = 1 + np.sin(2 * np.pi * t)

    fig, ax = plt.subplots()
    ax.plot(t, s)

    ax.set(xlabel='time (s)', ylabel='voltage (mV)',
           title='About as simple as it gets, folks')
    ax.grid()
    return fig


if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment()
    main(mle)
