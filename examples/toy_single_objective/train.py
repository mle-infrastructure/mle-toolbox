import time
import random
import numpy as np
import matplotlib.pyplot as plt
from mle_toolbox import experiment


def train_your_net(
    epoch: int, seed_id: int, lrate: float, batch_size: int, arch: str
) -> (float, float):
    """Surrogate Objective w. optimum: lrate=0.2, batch_size=4, arch='conv'."""
    f1 = (lrate - 0.2) ** 2 + (batch_size - 4) ** 2 + (0 if arch == "conv" else 10)
    train_loss = f1 + seed_id * 0.5
    test_loss = f1 + seed_id * 0.5 + random.uniform(0, 0.3)
    return train_loss / epoch, test_loss / epoch


# @experiment decorator allows you to set the default configuration to load
# if no other configuration path is provided by command line input
@experiment("toy_single_objective/base_config_1.yaml")
def main(mle):
    """Example training 'loop' using MLE-Logging."""
    for epoch in range(1, 11):
        train_loss, test_loss = train_your_net(epoch, **mle.train_config)
        # Update & save the newest log - only if epoch % log_every_j_steps
        if mle.ready_to_log(epoch):
            mle.log.update(
                {"num_epochs": epoch},
                {"train_loss": train_loss, "test_loss": test_loss},
                save=True,
            )
    # Generate a sample plot and store it
    fig = plot_loss(mle.log.stats_log.stats_tracked["train_loss"])
    mle.log.save_plot(fig)
    time.sleep(5)


def plot_loss(l_t):
    """Mini Example Plot of the loss."""
    t = np.arange(1, len(l_t) + 1)
    fig, ax = plt.subplots()
    ax.plot(t, l_t)
    ax.set(xlabel=r"# Epochs", ylabel="Loss", title="Surrogate Objective")
    ax.grid()
    fig.tight_layout()
    return fig


if __name__ == "__main__":
    # Run the simulation/Experiment - if the @experiment decorator is used you
    # don't have to manually provide the mle class instance as an input
    # This will be automatically taken care off by the decorator
    main()
