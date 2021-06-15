import os
import shutil
import unittest
from mle_toolbox.hyperopt import (HyperoptLogger,
                                  GridHyperoptimisation,
                                  RandomHyperoptimisation)


class TestHyperSearch(unittest.TestCase):
    test_case = "ode"
    if test_case == "ode":
        job_filename = "examples/ode/run_ode_int.py"
        config_filename = "examples/ode/ode_int_config_1.json"
        eval_score_type = "integral"
        params_to_search = {"real":
                                {"x_0":
                                      {"begin": 1,
                                       "end": 10,
                                       "bins": 6}
                                }
                            }

    elif test_case == "mnist":
        job_filename = "examples/mnist/run_mnist_cnn.py"
        config_filename = "examples/mnist/mnist_cnn_config_1.json"
        eval_score_type = "test_accuracy"
        params_to_search = {"real":
                                {"l_rate":
                                      {"begin": 0.5,
                                       "end": 1,
                                       "bins": 6}
                                }
                            }

    job_arguments = None
    experiment_dir = "examples/experiments/"
    hyperlog_fname = "hyper_log.hdf5"

    def test_1_grid_search(self):
        """ Test spawning a single experiment - locally/remote. """
        shutil.rmtree(TestHyperSearch.experiment_dir,
                      ignore_errors=True)
        hyperlog_fname = os.path.join(TestHyperSearch.experiment_dir,
                                      TestHyperSearch.hyperlog_fname)
        hyper_log = HyperoptLogger(hyperlog_fname,
                                   max_target = True,
                                   verbose = True,
                                   reload = False)
        hyper_opt = GridHyperoptimisation(hyper_log,
                                          TestHyperSearch.job_arguments,
                                          TestHyperSearch.config_filename,
                                          TestHyperSearch.job_filename,
                                          TestHyperSearch.experiment_dir,
                                          TestHyperSearch.params_to_search,
                                          problem_type = "final",
                                          eval_score_type = TestHyperSearch.eval_score_type)
        hyper_opt.run_search(num_search_batches = 2,
                             num_iter_per_batch = 3,
                             num_evals_per_iter = 2)
        self.assertEqual(len(hyper_log), 6)

    def test_1_random_search(self):
        """ Test spawning a single experiment - locally/remote. """
        shutil.rmtree(TestHyperSearch.experiment_dir,
                      ignore_errors=True)
        hyperlog_fname = os.path.join(TestHyperSearch.experiment_dir,
                                      TestHyperSearch.hyperlog_fname)
        hyper_log = HyperoptLogger(hyperlog_fname,
                                   max_target = True,
                                   verbose = True,
                                   reload = False)
        hyper_opt = RandomHyperoptimisation(hyper_log,
                                          TestHyperSearch.job_arguments,
                                          TestHyperSearch.config_filename,
                                          TestHyperSearch.job_filename,
                                          TestHyperSearch.experiment_dir,
                                          TestHyperSearch.params_to_search,
                                          problem_type = "final",
                                          eval_score_type = TestHyperSearch.eval_score_type)
        hyper_opt.run_search(num_search_batches = 2,
                             num_iter_per_batch = 3,
                             num_evals_per_iter = 2)
        self.assertEqual(len(hyper_log), 6)


if __name__ == '__main__':
    unittest.main()
