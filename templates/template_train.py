""" TEMPLATE FOR TRAINING SCRIPT FOR MLE-TOOLBOX W. LOGGING,
    ETC. - HERE TORCH EXAMPLE BUT TOOLBOX IS UNIVERSAL. """
import torch
from mle_toolbox import MLExperiment


def main(mle):
    """ Train a network. """
    # Set the training seed as well as the device to train on
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Define dataset, network, loss, optimizer to train on
    train_loader, test_loader = get_data()
    net = define_net().to(device)
    loss_fct = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(net.parameters(),
                                 lr=mle.train_config.l_rate,
                                 w_decay=mle.train_config.w_decay)

    # Train the network using the training loop
    train_net(mle,
              model=net, optimizer=optimizer,
              criterion=loss_fct, device=device,
              train_loader=train_loader,
              test_loader=test_loader)
    return


def define_net():
    """ Boilerplate for constructing a neural net. """
    return


def train_net(mle, model, optimizer, criterion, device,
              train_loader, test_loader, train_log):
    """ Run the training loop over a set of epochs. """
    for epoch in range(1, mle.train_config.num_epochs + 1):
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

        time_tick = {"epoch": epoch}
        stats_tick = {"train_loss": train_loss,
                      "test_loss": test_loss}
        mle.update_log(time_tick, stats_tick, model, save=True)

    return model, train_log


if __name__ == "__main__":
    mle = MLExperiment("configs/config_1.json")
    main(mle)
