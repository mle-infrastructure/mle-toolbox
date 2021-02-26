from sklearn import datasets, svm, metrics
from sklearn.model_selection import train_test_split
from mle_toolbox.utils import get_configs_ready, DeepLogger, set_random_seeds


def main(net_config, train_config, log_config):
    """ Train and log a simple SVM classifier. """
    # Set random seed and initialize logger instance
    set_random_seeds(seed_id=train_config.seed_id, verbose=False)
    train_log = DeepLogger(**log_config)

    # Load downsampled images and flatten them
    digits = datasets.load_digits()
    n_samples = len(digits.images)
    data = digits.images.reshape((n_samples, -1))

    # Split data into 50% train and 50% test subsets
    X_train, X_test, y_train, y_test = train_test_split(
        data, digits.target, test_size=0.5, shuffle=False)

    # Create a classifier: a support vector classifier
    clf = svm.SVC(gamma=train_config.svm_gamma)

    # Learn the digits on the train subset
    clf.fit(X_train, y_train)

    # Obtain predictions and compute accuracy
    train_predicted = clf.predict(X_train)
    train_acc = metrics.accuracy_score(train_predicted, y_train)
    test_predicted = clf.predict(X_test)
    test_acc = metrics.accuracy_score(test_predicted, y_test)

    # Log the results to the logger
    time_tic = [0]
    stats_tic = [train_acc, test_acc]
    train_log.update_log(time_tic, stats_tic, model=clf, save=True)


if __name__ == "__main__":
    train_config, net_config, log_config = get_configs_ready(
        default_config_fname="sklearn_svm/svm_config.json")

    main(net_config, train_config, log_config)
