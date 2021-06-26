import numpy as np
import matplotlib.pyplot as plt
from mle_toolbox import MLExperiment


def main(mle):
    """ Euler integrate a simple ODE for a specified length of time steps. """
    # Define function to integrate & run the integration
    def func(x):
        return -0.01*x

    # Let seed determine initial condition
    x_t = [mle.train_config.x_0]
    t_seq = np.arange(mle.train_config.dt,
                      mle.train_config.t_max,
                      mle.train_config.dt).tolist()

    for i, t in enumerate(t_seq):
        integral_det = x_t[-1] + func(x_t[-1]) * mle.train_config.dt
        integral_stoch = ((mle.train_config.noise_mean +
                          mle.train_config.noise_std* np.random.normal()) *
                          mle.train_config.dt)
        x_t.append(integral_det + integral_stoch)

        # Update & save the newest log
        if (i % mle.train_config.log_every_steps) == 0:
            time_tick = {"step_counter": i+1}
            stats_tick = {"integral": x_t[-1],
                          "noise": np.random.normal()}
            mle.update_log(time_tick, stats_tick, save=True)

    # Generate a sample plot and store it
    fig = plot_pde(x_t)
    mle.log.save_plot(fig, "_pde_integral.png")
    return


def plot_pde(x_t):
    """ Mini Example Plot of the PDE. """
    t = np.arange(len(x_t))
    fig, ax = plt.subplots()
    ax.plot(t, x_t)
    ax.set(xlabel=r'Time ($\Delta t$)', ylabel='PDE Value', title='PDE Trace')
    ax.grid()
    return fig



if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment()
    main(mle)
