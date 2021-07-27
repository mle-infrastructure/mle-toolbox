import unittest
import os
import shutil
import datetime
from mle_toolbox.experiment import Experiment


resource_to_run = "local"
job_filename = "examples/numpy_pde/run_pde_int.py"
config_filename = "examples/numpy_pde/pde_int_config_1.json"
job_arguments = {"env_name": "venv-mle-toolbox"}
experiment_dir = "examples/experiments/"


def test_experiment() -> None:
    """ Test Experiment class - Run PDE experiment on local machine. """
    timestr = datetime.datetime.today().strftime("%Y-%m-%d")[2:] + "_"
    base_str = os.path.split(config_filename)[1].split(".")[0]
    dir_to_check = os.path.join(experiment_dir, timestr + base_str + "/")
    if os.path.exists(dir_to_check) and os.path.isdir(dir_to_check):
        shutil.rmtree(dir_to_check)

    # Execute experiment 'job'
    experiment = Experiment(resource_to_run,
                            job_filename,
                            config_filename,
                            job_arguments,
                            experiment_dir)
    status_out = experiment.run()

    # Check that status of experiment is 0 (job completed)
    assert not status_out
    # Check that experiment directory with results exists
    assert os.path.exists(dir_to_check)
    # Check that copied .json config exists
    assert os.path.exists(os.path.join(dir_to_check,
                                       timestr +
                                       os.path.split(config_filename)[1]))
    # Check that log file exists
    assert os.path.exists(os.path.join(dir_to_check, "logs",
                                       timestr + base_str + "_seed_0.hdf5"))
    # Check that figure file exists
    assert os.path.exists(os.path.join(dir_to_check,
                                       "figures/fig_1_seed_0_pde_integral.png"))


if __name__ == '__main__':
    unittest.main()
