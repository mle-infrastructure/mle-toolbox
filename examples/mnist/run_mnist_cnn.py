import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import datasets, transforms
from mle_toolbox.utils import get_configs_ready, DeepLogger


def main(net_config, train_config, log_config):
    """ Train a network on MNIST dataset. """
    # Start by setting number of cores available to torch processes
    torch.set_num_threads(train_config.torch_num_threads)

    # Set the training seed as well as the device to train on
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Define the dataloaders (download the )
    train_loader = torch.utils.data.DataLoader(
        datasets.MNIST('../data', train=True, download=True,
                       transform=transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize((0.1307,), (0.3081,))
                       ])),
        batch_size=train_config.train_batch_size,
        num_workers=5, pin_memory=True, shuffle=True)

    test_loader = torch.utils.data.DataLoader(
        datasets.MNIST('../data', train=False, transform=transforms.Compose([
                           transforms.ToTensor(),
                           transforms.Normalize((0.1307,), (0.3081,))
                       ])),
        batch_size=train_config.test_batch_size,
        num_workers=5, pin_memory=True, shuffle=True)

    # Define the network architecture, loss function, optimizer & logger
    if train_config.net_type == "CNN":
        mnist_net = MNIST_CNN(net_config.dropout_prob,
                              net_config.hidden_fc_dim).to(device)
    elif train_config.net_type == "MLP":
        mnist_net = MNIST_MLP(net_config.dropout_prob,
                              net_config.hidden_fc_dim).to(device)

    nll_loss = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(mnist_net.parameters(), lr=train_config.l_rate)
    run_log = DeepLogger(**log_config)

    # Train the MNIST Network using the training loop
    train_mnist_cnn(num_epochs=train_config.num_epochs,
                    model=mnist_net, optimizer=optimizer,
                    criterion=nll_loss, device=device,
                    train_loader=train_loader,
                    test_loader=test_loader, train_log=run_log)
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


def train_mnist_cnn(num_epochs, model, optimizer, criterion, device,
                    train_loader, test_loader, train_log):
    """ Run the training loop over a set of epochs. """
    for epoch in range(1, num_epochs + 1):
        train_epoch_loss, test_epoch_loss = [], []
        model.train() # prep model for training
        for data, target in train_loader:
            optimizer.zero_grad()
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            loss.backward()
            optimizer.step()
            train_epoch_loss.append(loss.item())

        # Evaluate the model performance at end of epoch
        model.eval() # prep model for evaluation
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            loss = criterion(output, target)
            test_epoch_loss.append(loss.item())

        # Log average epoch losses
        train_loss = np.mean(train_epoch_loss)
        test_loss = np.mean(test_epoch_loss)

        time_tick = [epoch]
        stats_tick = [train_loss, test_loss]
        train_log.update_log(time_tick, stats_tick)
        train_log.save_log()
        train_log.save_network(model)

    return  model, train_log


if __name__ == "__main__":
    train_config, net_config, log_config = get_configs_ready(default_config_fname="mnist_cnn_config_1.json")

    main(net_config, train_config, log_config)
