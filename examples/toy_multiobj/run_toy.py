import time
from mle_toolbox import MLExperiment


def main(mle):
    """ Surrogate multi-objective training function. """
    # Define surrogate training function
    def fake_training(lrate, batch_size, arch):
        # optimal for learning_rate=0.2, batch_size=4, architecture="conv"
        f1 = ((lrate - 0.2) ** 2 + (batch_size - 4) ** 2
              + (0 if arch == "conv" else 10))
        # optimal for learning_rate=0.3, batch_size=2, architecture="mlp"
        f2 = ((lrate - 0.3) ** 2 + (batch_size - 2) ** 2
              + (0 if arch == "mlp" else 5))
        return f1, f2

    objective_1, objective_2 = fake_training(mle.train_config.lrate,
                                             mle.train_config.batch_size,
                                             mle.train_config.architecture)

    # Update & save the log
    time_tick = {"step_counter": 10}
    stats_tick = {"objective_1": objective_1,
                  "objective_2": objective_2}
    mle.update_log(time_tick, stats_tick, save=True)
    time.sleep(5)
    return


if __name__ == "__main__":
    # Run the simulation/Experiment
    mle = MLExperiment(default_config_fname="toy_multiobj/toy_config.yaml")
    main(mle)
