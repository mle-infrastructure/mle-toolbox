import unittest
import os
import shutil
import glob
import datetime
import subprocess as sp
from mle_toolbox.launch.search_experiment import run_hyperparameter_search


resource_to_run = "local"
experiment_dir = "examples/experiments/grid_sync"
meta_job_args = {"base_train_fname": "examples/numpy_pde/run_pde_int.py",
                 "base_train_config": "examples/numpy_pde/pde_int_config_1.json"}

search_logging = {"reload_log": False,
                  "verbose_log": True,
                  "max_objective": True,
                  "aggregate_seeds": "p50",
                  "problem_type": "final",
                  "eval_metrics": ["integral", "noise"]}

search_resources = {"num_search_batches": 2,
                    "num_evals_per_batch": 2,
                    "num_seeds_per_eval": 2,
                    "random_seeds": [1, 4]}

search_config = {
    "search_type": "grid",
    "search_schedule": "sync",
    "search_params": {
        "real": {"x_0": {"begin": 1,
                         "end": 10,
                         "bins": 2},
                 "noise_mean": {"begin": 0,
                                "end": 0.01,
                                "bins": 2}
                 }
    }
}

param_search_args = {"search_logging": search_logging,
                     "search_resources": search_resources,
                     "search_config": search_config}
single_job_args = {}

experiment_dir = "examples/experiments/grid_sync"


def check_correct_results(experiment_dir: str) -> None:
    """ Ensure that correct results and directories were generated. """
    assert os.path.exists(experiment_dir)
    # Check that json config, hyper and meta logs were created
    assert os.path.exists(os.path.join(experiment_dir, "hyper_log.pkl"))
    assert os.path.exists(os.path.join(experiment_dir, "meta_log.hdf5"))
    assert os.path.exists(os.path.join(experiment_dir, "search_base_config.json"))


def test_run_grid_sync() -> None:
    """ Test job launch wrapper - Run PDE experiment on local machine. """
    exp_dir = os.path.join(experiment_dir, "run_test")
    meta_job_args["experiment_dir"] = exp_dir
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    run_hyperparameter_search(
        resource_to_run,
        meta_job_args,
        single_job_args,
        param_search_args)

    check_correct_results(exp_dir)


def test_api_grid_sync() -> None:
    """ Execute `mle run pde_grid_sync.yaml` and check running pipeline. """
    os.chdir('./examples')
    exp_dir = "experiments/grid_sync/api_test"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = ("mle run numpy_pde/pde_search_grid.yaml -nw -np -resource local"
                   f" --experiment_dir {exp_dir}")

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    check_correct_results(exp_dir)
    os.chdir('..')
