import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
from mle_toolbox import MLExperiment


def main(mle):
    """Train a network on MNIST dataset."""
    # Start by setting number of cores available to torch processes
    torch.set_num_threads(mle.train_config.torch_num_threads)

    # Set the training seed as well as the device to train on
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Define the dataloaders (download the )
    train_loader = torch.utils.data.DataLoader(
        datasets.MNIST(
            "../data",
            train=True,
            download=True,
            transform=transforms.Compose(
                [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
            ),
        ),
        batch_size=mle.train_config.train_batch_size,
        num_workers=5,
        pin_memory=True,
        shuffle=True,
    )

    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST(
            "../data",
            train=False,
            transform=transforms.Compose(
                [transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))]
            ),
        ),
        batch_size=mle.train_config.test_batch_size,
        num_workers=5,
        pin_memory=True,
        shuffle=True,
    )

    # Define the network architecture, loss function, optimizer & logger
    if mle.train_config.net_type == "CNN":
        mnist_net = MNIST_CNN(
            mle.model_config.dropout_prob, mle.model_config.hidden_fc_dim
        ).to(device)
    elif mle.train_config.net_type == "MLP":
        mnist_net = MNIST_MLP(
            mle.model_config.dropout_prob, mle.model_config.hidden_fc_dim
        ).to(device)

    nll_loss = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(mnist_net.parameters(), lr=mle.train_config.l_rate)

    # Train the MNIST Network using the training loop
    train_mnist_network(
        mle,
        model=mnist_net,
        optimizer=optimizer,
        criterion=nll_loss,
        device=device,
        train_loader=train_loader,
        test_loader=test_loader,
    )
    return


class MNIST_CNN(nn.Module):
    def __init__(self, dropout_prob=0.5, hidden_fc_dim=128):
        super(MNIST_CNN, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout = nn.Dropout2d(dropout_prob)
        self.fc1 = nn.Linear(9216, hidden_fc_dim)
        self.fc2 = nn.Linear(hidden_fc_dim, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.fc2(x)
        return x


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


def train_mnist_network(
    mle, model, optimizer, criterion, device, train_loader, test_loader
):
    """Run the training loop over a set of epochs."""
    update_counter = 0
    train_losses = []
    while True:
        model.train()  # prep model for training
        for data, target in train_loader:
            optimizer.zero_grad()
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()

            train_losses.append(loss.item())
            update_counter += 1

            if update_counter % 50 == 0 or update_counter == 1:
                test_loss = evaluate_network(model, test_loader, device, criterion)
                time_tick = {"num_updates": update_counter}
                stats_tick = {
                    "train_loss": np.mean(train_losses),
                    "test_loss": test_loss,
                }
                mle.update_log(time_tick, stats_tick, model=model, save=True)

            # Stop training if number of steps is 'ready' number reached!
            if update_counter == mle.train_config.total_num_updates:
                return


def evaluate_network(model, test_loader, device, criterion):
    # Evaluate the model performance at end of epoch
    model.eval()  # prep model for evaluation
    eval_loss = []
    for data, target in test_loader:
        data, target = data.to(device), target.to(device)
        output = model(data)
        loss = criterion(output, target)
        eval_loss.append(loss.item())
    # Log average epoch losses
    test_loss = np.mean(eval_loss)
    # Put network back into training mode
    model.train()
    return test_loss


if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment()
    main(mle)
