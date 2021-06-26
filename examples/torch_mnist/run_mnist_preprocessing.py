import os
import argparse
import matplotlib.pyplot as plt
from torchvision import datasets, transforms


def mnist_preprocessing(figures_dir):
    """ Some preprocessing - E.g. generate a MNIST input plot. """
    # As torch.Tensor
    dataset = datasets.MNIST('../data',
                             transform=transforms.ToTensor())
    x, _ = dataset[7777] # x is now a torch.Tensor
    plt.imshow(x.numpy()[0], cmap='gray')
    plt.title('A MNIST Digit')

    # Create a new empty directory for the figure
    if not os.path.exists(figures_dir):
        try: os.makedirs(figures_dir)
        except: pass
    plt.savefig(os.path.join(figures_dir, 'mnist_digit.png'), dpi=300)
    return


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
    mnist_preprocessing(cmd_args.figures_dir)
