import unittest
import os
import shutil
import glob
import datetime
import subprocess as sp
from mle_toolbox.experiment import ExperimentQueue
from mle_toolbox.launch.multi_config import run_multiple_configs


resource_to_run = "local"
job_filename = "examples/numpy_pde/run_pde_int.py"
config_filenames = ["examples/numpy_pde/pde_int_config_1.json",
                    "examples/numpy_pde/pde_int_config_2.json"]
job_arguments = {}
num_seeds = num_configs = 2
random_seeds = [2, 3]
experiment_dir = "examples/experiments/multi"


def check_correct_results(experiment_dir, config_filename) -> None:
    """ Ensure that correct results and directories were generated. """
    timestr = datetime.datetime.today().strftime("%Y-%m-%d")[2:] + "_"
    base_str = os.path.split(config_filename)[1].split(".")[0]
    dir_to_check = os.path.join(experiment_dir, timestr + base_str + "/")

    # Check that experiment directory with results exists
    assert os.path.exists(dir_to_check)
    # Check that copied .json config exists
    assert os.path.exists(os.path.join(dir_to_check,
                                       timestr +
                                       os.path.split(config_filename)[1]))
    # Check that log file exists
    assert os.path.exists(os.path.join(dir_to_check, "logs",
                                       base_str + ".hdf5"))
    # Check that figure files exist
    png_counter = len(glob.glob1(os.path.join(dir_to_check,
                                              "figures/"), "*.png"))

    assert png_counter == num_seeds


def test_experiment_queue() -> None:
    """ Test `ExperimentQueue` class for correct result generation. """
    exp_dir = os.path.join(experiment_dir, "queue_test")
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Run Experiment Jobs in Batch mode!
    default_seed = 0
    multi_experiment = ExperimentQueue(
        resource_to_run,
        job_filename,
        config_filenames,
        job_arguments,
        exp_dir,
        num_seeds,
        default_seed,
        random_seeds,
        num_seeds * num_configs,
    )
    multi_experiment.run()

    # Check that all results for different configs were generated
    for cfname in config_filenames:
        check_correct_results(exp_dir, cfname)


def test_run_multi() -> None:
    """ Test multi config job launch wrapper - Run PDE experiment on local machine. """
    exp_dir = os.path.join(experiment_dir, "run_test")
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    run_multiple_configs(
        resource_to_run,
        meta_job_args={"base_train_fname": job_filename,
                       "experiment_dir": exp_dir},
        single_job_args={},
        multi_config_args={"config_fnames": config_filenames,
                           "num_seeds": num_seeds,
                           "random_seeds": random_seeds},
    )

    # Check that all results for different configs were generated
    for cfname in config_filenames:
        check_correct_results(exp_dir, cfname)


def test_api_multi() -> None:
    """ Execute `mle run pde_multi.yaml` and check running pipeline. """
    os.chdir('./examples')
    exp_dir = "experiments/multi/api_test"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = ("mle run numpy_pde/pde_configs.yaml -nw -np -resource local"
                   f" --experiment_dir {exp_dir}")

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    for cfname in config_filenames:
        check_correct_results(exp_dir, cfname)
    os.chdir('..')
