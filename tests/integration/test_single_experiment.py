import unittest
from mle_toolbox.experiment import Experiment


class TestExperiment(unittest.TestCase):
    test_case = "ode"
    if test_case == "ode":
        job_filename = "examples/ode/run_ode_int.py"
        config_filename = "examples/ode/ode_int_config_1.json"
    elif test_case == "mnist":
        job_filename = "examples/mnist/run_mnist_cnn.py"
        config_filename = "examples/mnist/mnist_cnn_config_1.json"
    elif test_case == "ppo":
        job_filename = "examples/ppo/run_ppo.py"
        config_filename = "examples/ppo/base_ppo_config.json"

    job_arguments = None
    experiment_dir = "examples/experiments/"

    def test_experiment(self):
        """ Test Experiment class - Run ODE experiment locally/remote. """
        experiment = Experiment(TestExperiment.job_filename,
                                TestExperiment.config_filename,
                                TestExperiment.job_arguments,
                                TestExperiment.experiment_dir)
        status_out = experiment.run()
        self.assertEqual(0, status_out)


if __name__ == '__main__':
    unittest.main()
