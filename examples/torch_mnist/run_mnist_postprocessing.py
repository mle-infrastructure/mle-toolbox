import argparse


def mnist_postprocessing(log_dir, figures_dir):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-log_dir', '--log_dir',
                        default='experiments/',
                        help='Experiment Directory.')
    cmd_args = parser.parse_args()
    mnist_postprocessing(cmd_args.experiment_dir,
                         cmd_args.preproc_plot)
