import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
from mle_toolbox import MLExperiment


def main(mle):
    """ Train a network on MNIST dataset. """
    # Start by setting number of cores available to torch processes
    torch.set_num_threads(mle.train_config.torch_num_threads)

    # Set the training seed as well as the device to train on
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Define the dataloaders
    mnist_transform = transforms.Compose([transforms.ToTensor(),
                            transforms.Normalize((0.1307,), (0.3081,))])
    train_loader = torch.utils.data.DataLoader(
        datasets.MNIST('../data', train=True, download=True,
                       transform=mnist_transform),
        batch_size=mle.train_config.train_batch_size,
        num_workers=5, pin_memory=True, shuffle=True)

    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST('../data', train=False,
                       transform=mnist_transform),
        batch_size=mle.train_config.test_batch_size,
        num_workers=5, pin_memory=True, shuffle=True)

    # Define the network architecture, loss function, optimizer & logger
    mnist_net = MNIST_MLP(mle.model_config.dropout_prob,
                          mle.model_config.hidden_fc_dim).to(device)

    if mle.model_ckpt is not None:
        model.load_state_dict(mle.model_ckpt)

    nll_loss = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(mnist_net.parameters(),
                                 lr=mle.train_config.l_rate)

    # Train the MNIST Network using the training loop
    train_mnist_network(mle,
                        model=mnist_net,
                        optimizer=optimizer,
                        criterion=nll_loss,
                        device=device,
                        train_loader=train_loader,
                        test_loader=test_loader)
    return


class MNIST_MLP(nn.Module):
    def __init__(self, dropout_prob=0.5, hidden_fc_dim=128):
        super(MNIST_MLP, self).__init__()
        self.fc1 = nn.Linear(28 * 28, hidden_fc_dim)
        self.fc2 = nn.Linear(hidden_fc_dim, hidden_fc_dim)
        self.fc3 = nn.Linear(hidden_fc_dim, 10)
        self.dropout = nn.Dropout(0.5)

    def forward(self, x):
        x = x.view(-1, 28 * 28)
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = self.fc3(x)
        return x


def train_mnist_network(mle, model, optimizer, criterion, device,
                        train_loader, test_loader):
    """ Run the training loop over a set of epochs. """
    update_counter = 0
    train_losses = []

    model.train() # prep model for training
    while True:
        for data, target in train_loader:
            optimizer.zero_grad()
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            train_losses.append(loss.item())
            update_counter += 1

            # Update log with latest evaluation results
            if update_counter % mle.train_config.num_steps_until_eval == 0:
                test_loss = evaluate_network(model, test_loader,
                                             device, criterion)
                time_tick = {"num_updates": update_counter}
                stats_tick = {"train_loss": np.mean(train_losses),
                              "test_loss": test_loss}
                mle.update_log(time_tick, stats_tick, model=model, save=True)
                train_losses = []

            # Stop training if number of steps is 'ready' number reached!
            if update_counter == mle.train_config.num_steps_until_ready:
                return


def evaluate_network(model, test_loader, device, criterion):
    # Evaluate the model performance at end of epoch
    model.eval() # prep model for evaluation
    evals = 0
    eval_loss = []
    for data, target in test_loader:
        data, target = data.to(device), target.to(device)
        output = model(data)
        loss = criterion(output, target)
        eval_loss.append(loss.item())
        evals += 1
    # Log average epoch losses
    test_loss = np.mean(eval_loss)
    # Put network back into training mode
    model.train()
    return test_loss


if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment()
    main(mle)
