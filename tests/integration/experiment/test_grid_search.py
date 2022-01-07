import os
import shutil
import subprocess as sp
from mle_toolbox.launch.search_experiment import run_hyperparameter_search


resource_to_run = "local"
experiment_dir = "examples/experiments/grid"
meta_job_args = {
    "base_train_fname": "examples/toy_single_objective/train.py",
    "base_train_config": "examples/toy_single_objective/base_config_1.yaml",
}

search_logging = {
    "reload_log": False,
    "max_objective": False,
    "aggregate_seeds": "p50",
    "problem_type": "final",
    "eval_metrics": "test_loss",
}

search_resources_sync = {
    "num_search_batches": 2,
    "num_evals_per_batch": 2,
    "num_seeds_per_eval": 2,
    "random_seeds": [1, 4],
}

search_resources_async = {
    "num_total_evals": 4,
    "max_running_jobs": 4,
    "num_seeds_per_eval": 2,
    "random_seeds": [1, 4],
}

search_config = {
    "search_type": "Grid",
    "search_schedule": "sync",
    "search_params": {
        "real": {"lrate": {"begin": 0.1, "end": 0.4, "bins": 4}},
    },
}


single_job_args = {}


def check_correct_results(experiment_dir: str, api_check: bool = False) -> None:
    """Ensure that correct results and directories were generated."""
    assert os.path.exists(experiment_dir)
    # Check that json config, hyper and meta logs were created
    assert os.path.exists(os.path.join(experiment_dir, "hyper_log.pkl"))
    assert os.path.exists(os.path.join(experiment_dir, "meta_log.hdf5"))
    assert os.path.exists(os.path.join(experiment_dir, "search_base_config.yaml"))

    # Check that experiment config yaml was created (reproducibility)
    if api_check:
        assert os.path.exists(os.path.join(experiment_dir, "experiment_config.yaml"))


def test_run_grid_sync() -> None:
    """Test job launch wrapper - Run PDE experiment on local machine."""
    exp_dir = os.path.join(experiment_dir, "run_sync_test")
    meta_job_args["experiment_dir"] = exp_dir
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    param_search_args = {
        "search_logging": search_logging,
        "search_resources": search_resources_sync,
        "search_config": search_config,
    }
    param_search_args["search_config"]["search_schedule"] = "sync"

    run_hyperparameter_search(
        resource_to_run, meta_job_args, single_job_args, param_search_args
    )

    check_correct_results(exp_dir)


def test_run_grid_async() -> None:
    """Test job launch wrapper - Run PDE experiment on local machine."""
    exp_dir = os.path.join(experiment_dir, "run_async_test")
    meta_job_args["experiment_dir"] = exp_dir
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    param_search_args = {
        "search_logging": search_logging,
        "search_resources": search_resources_async,
        "search_config": search_config,
    }
    param_search_args["search_config"]["search_schedule"] = "async"

    run_hyperparameter_search(
        resource_to_run, meta_job_args, single_job_args, param_search_args
    )

    check_correct_results(exp_dir)


def test_api_grid_sync() -> None:
    """Execute `mle run pde_grid_sync.yaml` and check running pipeline."""
    os.chdir("./examples")
    exp_dir = "experiments/grid/api_test"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = (
        "mle run toy_single_objective/mle_search_grid.yaml -nw -np -resource local"
        f" --experiment_dir {exp_dir}"
    )

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    check_correct_results(exp_dir, api_check=True)
    os.chdir("..")
