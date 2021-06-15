import os
import shutil
import unittest
from mle_toolbox.multi_runner import spawn_multiple_runs


class TestMultipleExperiments(unittest.TestCase):
    test_case = "ode"
    if test_case == "ode":
        job_filename = "examples/ode/run_ode_int.py"
        config_filenames = ["examples/ode/ode_int_config_1.json",
                            "examples/ode/ode_int_config_2.json"]
    elif test_case == "mnist":
        job_filename = "examples/mnist/run_mnist_cnn.py"
        config_filenames = ["examples/mnist/mnist_cnn_config_1.json",
                            "examples/mnist/mnist_cnn_config_2.json"]

    job_arguments = None
    experiment_dir = "examples/experiments/"
    num_seeds = 2

    def test_1_single_experiment(self):
        """ Test spawning a single experiment - locally/remote. """
        shutil.rmtree(TestMultipleExperiments.experiment_dir,
                      ignore_errors=True)
        spawn_multiple_runs(TestMultipleExperiments.job_filename,
                            TestMultipleExperiments.config_filenames[0],
                            TestMultipleExperiments.job_arguments,
                            TestMultipleExperiments.experiment_dir,
                            num_seeds=1)
        self.assertEqual(0, 0)

    def test_2_multiple_seeds(self):
        """ Test running exp. for different rahdom seeds - locally/remote. """
        shutil.rmtree(TestMultipleExperiments.experiment_dir,
                      ignore_errors=True)
        spawn_multiple_runs(TestMultipleExperiments.job_filename,
                            TestMultipleExperiments.config_filenames[0],
                            TestMultipleExperiments.job_arguments,
                            TestMultipleExperiments.experiment_dir,
                            TestMultipleExperiments.num_seeds)
        self.assertEqual(0, 0)

    def test_3_multiple_configs(self):
        """ Test running exp. for different .json configs - locally/remote. """
        shutil.rmtree(TestMultipleExperiments.experiment_dir,
                      ignore_errors=True)
        spawn_multiple_runs(TestMultipleExperiments.job_filename,
                            TestMultipleExperiments.config_filenames,
                            TestMultipleExperiments.job_arguments,
                            TestMultipleExperiments.experiment_dir)
        self.assertEqual(0, 0)

    def test_4_multiple_configs_seeds(self):
        """ Test running exp. for diff. configs + seeds - locally/remote. """
        shutil.rmtree(TestMultipleExperiments.experiment_dir,
                      ignore_errors=True)
        spawn_multiple_runs(TestMultipleExperiments.job_filename,
                            TestMultipleExperiments.config_filenames,
                            TestMultipleExperiments.job_arguments,
                            TestMultipleExperiments.experiment_dir,
                            TestMultipleExperiments.num_seeds)
        self.assertEqual(0, 0)


if __name__ == '__main__':
    unittest.main()
