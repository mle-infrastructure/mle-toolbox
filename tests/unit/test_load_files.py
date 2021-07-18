import unittest
import os
from dotmap import DotMap
from mle_toolbox.utils import (load_yaml_config,
                               load_json_config,
                               load_mle_toolbox_config,
                               load_result_logs)
from mle_toolbox.utils import load_hyper_log
from mle_toolbox.utils import load_meta_log


cmd_args_proxy = DotMap({
                "config_fname": "tests/fixtures/test_yaml_config.yaml",
                "base_train_fname": "tests/fixtures/test_python_script.py",
                "base_train_config": "tests/fixtures/test_json_config.json",
                "experiment_dir": "experiments/"})

mle_config_fname = "tests/test_mle_config.toml"
meta_log_fname = "test_meta_log.hdf5"
hyper_log_fname = "test_hyper_log.pkl"


class TestFileLoading(unittest.TestCase):
    def test_load_json_config(self):
        """ Make sure that assert is raised since no `log_config` is given. """
        with self.assertRaises(AssertionError):
            json_config = load_json_config(cmd_args_proxy.base_train_config)

    def test_load_yaml_config(self):
        """ Assert manual inputs are written to experiment configuration. """
        experiment_config = load_yaml_config(cmd_args_proxy)
        assert (experiment_config.meta_job_args.base_train_fname ==
                cmd_args_proxy.base_train_fname)
        assert (experiment_config.meta_job_args.base_train_config ==
                cmd_args_proxy.base_train_config)
        assert (experiment_config.meta_job_args.experiment_dir ==
                cmd_args_proxy.experiment_dir)

    def test_load_mle_config(self):
        """ Assert correct loading of mle config .toml file. """
        mle_config = load_mle_toolbox_config(mle_config_fname)

    def test_load_result_logs(self):
        """ Assert correct loading of hyper/meta log files. """
        meta, hyper = load_result_logs("tests/fixtures",
                                       meta_log_fname,
                                       hyper_log_fname)

    def test_load_meta_log(self):
        meta = load_meta_log(os.path.join("tests/fixtures",
                                          meta_log_fname))

    def test_load_hyper_log(self):
        hyper = load_hyper_log(os.path.join("tests/fixtures",
                                            hyper_log_fname))
