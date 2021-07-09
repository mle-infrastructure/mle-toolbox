import unittest
from dotmap import DotMap
from mle_toolbox.utils import load_yaml_config

cmd_args_proxy = DotMap({
                "config_fname": "tests/assets/test_yaml_config.yaml",
                "base_train_fname": "tests/assets/test_python_script.py",
                "base_train_config": "tests/assets/test_json_config.json",
                "experiment_dir": "experiments/"})


def test_load_yaml_config():
    experiment_config = load_yaml_config(cmd_args_proxy)
    assert (experiment_config.meta_job_args.base_train_fname ==
            cmd_args_proxy.base_train_fname)
    assert (experiment_config.meta_job_args.base_train_config ==
            cmd_args_proxy.base_train_config)
    assert (experiment_config.meta_job_args.experiment_dir ==
            cmd_args_proxy.experiment_dir)
