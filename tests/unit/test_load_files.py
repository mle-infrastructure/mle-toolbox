import unittest
from dotmap import DotMap
from mle_toolbox.utils import (load_yaml_config,
                               load_json_config,
                               load_mle_toolbox_config)


cmd_args_proxy = DotMap({
                "config_fname": "tests/fixtures/test_yaml_config.yaml",
                "base_train_fname": "tests/fixtures/test_python_script.py",
                "base_train_config": "tests/fixtures/test_json_config.json",
                "experiment_dir": "experiments/"})


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
        config_fname = "tests/test_mle_config.toml"
        mle_config = load_mle_toolbox_config(config_fname)

    def test_load_meta_log(self):
        return

    def test_load_hyper_log(self):
        return
