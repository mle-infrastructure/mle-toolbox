import argparse
import os
from mle_toolbox.utils import load_run_log
import matplotlib.pyplot as plt


def mnist_postprocessing(experiment_dir, figures_dir):
    """ Some postprocessing - E.g. generate a learning curve plot. """
    # Find directory in which experiment results are stored + load log
    sub_dirs = [f.path for f in os.scandir(experiment_dir) if f.is_dir()]
    result_dir = [d for d in sub_dirs if d.endswith("mnist_cnn_config_1")][0]
    loaded_log = load_run_log(result_dir)
    fig, ax = plt.subplots()
    ax.plot(loaded_log.meta_log.time.num_updates,
            loaded_log.meta_log.stats.test_loss)
    ax.set_xlabel("Number of Batch Updates")
    ax.set_ylabel("Test Loss")
    ax.set_title("MNIST CNN Test Loss")
    fig.savefig(os.path.join(figures_dir,
                             "mnist_learning_curve.png"), dpi=300)


if __name__ == '__main__':
    # Experiment directory is always provided as cmd input!!
    # Other arguments have to provide full key: -figures_dir and not fig_dir
    parser = argparse.ArgumentParser()
    parser.add_argument('-exp_dir', '--experiment_dir',
                        default='experiments',
                        help='Figures Directory.')
    parser.add_argument('-figures_dir', '--figures_dir',
                        default='experiments/figures',
                        help='Figures Directory.')
    cmd_args = parser.parse_args()
    mnist_postprocessing(cmd_args.experiment_dir,
                         cmd_args.figures_dir)
