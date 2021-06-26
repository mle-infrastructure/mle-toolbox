import argparse


def mnist_preprocessing(experiment_dir,):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-exp_dir', '--experiment_dir',
                        default='experiment/mnist',
                        help='Experiment Directory.')
    parser.add_argument('-exp_dir', '--figures_dir',
                        default='experiment/mnist',
                        help='Experiment Directory.')
    cmd_args = parser.parse_args()
    mnist_preprocessing(cmd_args.experiment_dir,
                        cmd_args.preproc_plot)
