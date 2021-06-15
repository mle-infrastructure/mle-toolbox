import os
import shutil
import unittest
from mle_toolbox.hyperopt import HyperoptLogger, SMBOHyperoptimisation


class TestHyperSMBO(unittest.TestCase):
    test_case = "ode"
    if test_case == "ode":
        job_filename = "examples/ode/run_ode_int.py"
        config_filename = "examples/ode/ode_int_config_1.json"
        eval_score_type = "integral"
        params_to_search = {"real":
                                {"x_0":
                                      {"begin": 1,
                                       "end": 10,
                                       "prior": "log-uniform"}
                                }
                            }

    smbo_config = {"base_estimator": "GP",
                   "acq_function": "gp_hedge",
                   "n_initial_points": 6}
    job_arguments = None
    experiment_dir = "examples/experiments/"
    hyperlog_fname = "hyper_log.hdf5"

    def test_smbo_search(self):
        """ Test spawning a single experiment - locally/remote. """
        shutil.rmtree(TestHyperSMBO.experiment_dir,
                      ignore_errors=True)
        hyperlog_fname = os.path.join(TestHyperSMBO.experiment_dir,
                                      TestHyperSMBO.hyperlog_fname)
        hyper_log = HyperoptLogger(hyperlog_fname,
                                   max_target = True,
                                   verbose = True,
                                   reload = False)
        hyper_opt = SMBOHyperoptimisation(hyper_log,
                                          TestHyperSMBO.job_arguments,
                                          TestHyperSMBO.config_filename,
                                          TestHyperSMBO.job_filename,
                                          TestHyperSMBO.experiment_dir,
                                          TestHyperSMBO.params_to_search,
                                          problem_type = "final",
                                          eval_score_type = TestHyperSMBO.eval_score_type,
                                          smbo_config = TestHyperSMBO.smbo_config)
        hyper_opt.run_search(num_search_batches = 5,
                             num_iter_per_batch = 3,
                             num_evals_per_iter = 2)
        self.assertEqual(0, 0)


if __name__ == '__main__':
    unittest.main()
