import unittest
import os
from dotmap import DotMap
from mle_toolbox.utils import (load_experiment_config,
                               load_mle_toolbox_config,
                               load_result_logs,
                               load_hyper_log,
                               combine_experiments)
from mle_toolbox.hyperopt import HyperoptLogger
from mle_logging.load import load_meta_log


cmd_args_proxy = DotMap({
    "config_fname": "tests/unit/fixtures/yaml_config.yaml",
    "base_train_fname": "tests/unit/fixtures/python_script.py",
    "base_train_config": "tests/unit/fixtures/json_config.json",
    "experiment_dir": "experiments/"})

mle_config_fname = "tests/unit/fixtures/toolbox_config.toml"
meta_log_fname = "meta_log.hdf5"
hyper_log_fname = "hyper_log.pkl"


class TestFileLoading(unittest.TestCase):
    def test_load_yaml_config(self):
        """ Assert manual inputs are written to experiment configuration. """
        experiment_config = load_experiment_config(cmd_args_proxy)
        assert (experiment_config.meta_job_args.base_train_fname ==
                cmd_args_proxy.base_train_fname)
        assert (experiment_config.meta_job_args.base_train_config ==
                cmd_args_proxy.base_train_config)
        assert (experiment_config.meta_job_args.experiment_dir ==
                cmd_args_proxy.experiment_dir)

    def test_load_mle_config(self):
        """ Assert correct loading of mle config .toml file. """
        mle_config = load_mle_toolbox_config(mle_config_fname)
        assert type(mle_config) == DotMap

    def test_load_result_logs(self):
        """ Assert correct loading of hyper/meta log files. """
        meta, hyper = load_result_logs("tests/unit/fixtures/experiment_1",
                                       meta_log_fname,
                                       hyper_log_fname)

    def test_load_meta_log(self):
        """ Assert correct loading of meta log files. """
        meta = load_meta_log(os.path.join("tests/unit/fixtures/experiment_1",
                                          meta_log_fname))

    def test_load_hyper_log(self):
        """ Assert correct loading of hyper log files. """
        hyper = load_hyper_log(os.path.join("tests/unit/fixtures/experiment_1",
                                            hyper_log_fname))

    def test_reload_hyper_log(self):
        """ Assert correct reloading of hyper log files for continuation. """
        hyper = HyperoptLogger(
            hyperlog_fname=os.path.join("tests/unit/fixtures/experiment_1",
                                        hyper_log_fname),
            eval_metrics="integral",
            reload_log=True
        )
        assert hyper.iter_id == 4
        assert hyper.best_per_metric == {'integral': {'run_id': 4,
                                                      'score': 4.274364709854126,
                                                      'params': {'noise_mean': 0.01,
                                                                 'x_0': 10.0}}}

    def test_combine_experiments(self):
        """ Test loading of multiple experiment logs."""
        meta, hyper = combine_experiments(["tests/unit/fixtures/experiment_1",
                                           "tests/unit/fixtures/experiment_2"])
