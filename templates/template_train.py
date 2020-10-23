import torch
from mle_toolbox.utils import (set_random_seeds,
                               get_configs_ready,
                               DeepLogger)


def main(net_config, train_config, log_config):
    """ Train a network. """
    # Start by setting the random seeds for reproducibility
    set_random_seeds(train_config.seed_id)
    
    # Set the training seed as well as the device to train on
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Define dataset, network, loss, optimizer to train on
    train_loader, test_loader = get_data()
    net = define_network().to(device)
    loss_fct = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(net.parameters(),
                                 lr=train_config.l_rate,
                                 w_decay=train_config.w_decay)
    run_log = DeepLogger(**log_config)

    # Train the network using the training loop
    train_net(num_epochs=train_config.num_epochs,
              model=net, optimizer=optimizer,
              criterion=loss_fct, device=device,
              train_loader=train_loader,
              test_loader=test_loader, train_log=run_log)
    return


def train_net(num_epochs, model, optimizer, criterion, device,
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

    return model, train_log


if __name__ == "__main__":
    train_config, net_config, log_config = get_configs_ready(default_config_fname="configs/config_1.json")
    main(net_config, train_config, log_config)
