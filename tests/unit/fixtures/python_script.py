import os
import argparse
import numpy as np
import matplotlib.pyplot as plt


def processing(experiment_dir, figures_dir):
    """Some processing - E.g. plot a sine wave."""
    # As torch.Tensor
    x = np.arange(0, 10, 0.1)
    y = np.sin(x)
    plt.plot(x, y)
    plt.title("A Sine Wave")

    # Create a new empty directory for the figure
    save_figures_dir = os.path.join(experiment_dir, figures_dir)
    if not os.path.exists(save_figures_dir):
        try:
            os.makedirs(save_figures_dir)
        except:
            pass
    plt.savefig(os.path.join(save_figures_dir, "sine_wave.png"), dpi=300)
    return


if __name__ == "__main__":
    # Experiment directory is always provided as cmd input!!
    # Other arguments have to provide full key: -figures_dir and not fig_dir
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-exp_dir", "--experiment_dir", default="experiments", help="Figures Directory."
    )
    parser.add_argument(
        "-figures_dir", "--figures_dir", default="figures", help="Figures Directory."
    )
    cmd_args = parser.parse_args()
    processing(cmd_args.experiment_dir, cmd_args.figures_dir)
