import numpy as np
from mle_toolbox import MLExperiment


class QuadraticProblem(object):
    def __init__(self, theta=None, lrate: float = 0.1):
        self.lrate = lrate

    def step(self, h, theta):
        """Perform GradAscent step on quadratic surrogate objective (max!)."""
        surrogate_grad = -2.0 * h * theta
        return theta + self.lrate * surrogate_grad

    def evaluate(self, theta):
        """Ground truth objective (e.g. val loss) - Jaderberg et al. 2016."""
        return 1.2 - np.sum(theta ** 2)

    def surrogate_objective(self, h, theta):
        """Surrogate objective (with hyperparams h) - Jaderberg et al. 2016."""
        return 1.2 - np.sum(h * theta ** 2)

    def __call__(self, theta, hyperparams):
        h = np.array([hyperparams["h0"], hyperparams["h1"]])
        theta = self.step(h, theta)
        exact = self.evaluate(theta)
        # surrogate = self.surrogate_objective(h, theta)
        return theta.tolist(), exact


def main(mle):
    """Optimize a simple quadratic."""
    # Reload the 'weights' (theta) corresponding to quadratic
    if mle.model_ckpt is not None:
        theta = mle.model_ckpt
    else:
        theta = np.array(mle.train_config.theta_init)
    problem = QuadraticProblem()

    for update_counter in range(mle.train_config.extra.pbt_num_add_iters):
        theta, score = problem(theta, mle.train_config.params)
        # Update log with latest evaluation results
        time_tick = {
            "num_steps": update_counter + 1,
            "total_pbt_updates": mle.train_config.extra.pbt_num_total_iters
            - mle.train_config.extra.pbt_num_add_iters
            + update_counter
            + 1,
        }
        stats_tick = {
            "objective": score,
            "theta_0": theta[0],
            "theta_1": theta[1],
        }
        mle.update_log(time_tick, stats_tick, model=theta, save=True)
    return


if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment()
    main(mle)
