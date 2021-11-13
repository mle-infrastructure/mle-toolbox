import numpy as np
from mle_toolbox import MLExperiment


def main(mle):
    """Optimize a simple quadratic."""
    # Reload the 'weights' (theta) corresponding to quadratic
    if mle.model_ckpt is not None:
        theta = mle.model_ckpt
    else:
        theta = np.array(mle.train_config.theta_init[mle.train_config.worker_id])

    # Combine hyperparameters h0, h1 into np array
    h = np.stack([mle.train_config.h0, mle.train_config.h1])

    for update_counter in range(mle.train_config.num_steps_until_ready):
        theta = step(theta, h, mle.train_config.lrate)
        # Update log with latest evaluation results
        time_tick = {"num_updates": update_counter + 1}
        stats_tick = {
            "objective": evaluate(theta),
            "surrogate": surrogate_objective(theta, h),
            "theta_0": theta[0],
            "theta_1": theta[1],
        }
        mle.update_log(time_tick, stats_tick, model=theta, save=True)

    # Stop training if number of steps is 'ready' number reached!
    if (update_counter + 1) == mle.train_config.num_steps_until_ready:
        return

    return


def step(theta, h, lrate):
    """Perform GradAscent step on quadratic surrogate objective (maximize!)."""
    surrogate_grad = -2.0 * h * theta
    return theta + lrate * surrogate_grad


def evaluate(theta):
    """Ground truth objective (e.g. val loss) as in Jaderberg et al. 2016."""
    return 1.2 - np.sum(theta ** 2)


def surrogate_objective(theta, h):
    """Surrogate objective (with hyperparams h) as in Jaderberg et al. 2016."""
    return 1.2 - np.sum(h * theta ** 2)


if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment()
    main(mle)
