import os
import shutil
from mle_toolbox.launch.search_experiment import run_hyperparameter_search


resource_to_run = "local"
experiment_dir = "examples/experiments/pbt"
meta_job_args = {
    "base_train_fname": "examples/pbt_quadratic/run_quadratic_steps.py",
    "base_train_config": "examples/pbt_quadratic/quadratic_config.json",
}

search_logging = {
    "max_objective": True,
    "eval_metrics": "objective",
}

search_resources = {
    "num_search_batches": 3,
    "num_seeds_per_eval": 1,
}

search_config = {
    "search_type": "PBT",
    "search_params": {
        "real": {
            "h0": {"begin": 0.0, "end": 1.0, "prior": "uniform"},
            "h1": {"begin": 0.0, "end": 1.0, "prior": "uniform"},
        },
    },
    "search_config": {
        "num_workers": 2,
        "explore": {"strategy": "additive-noise", "noise_scale": 0.35},
        "exploit": {"strategy": "truncation", "selection_percent": 0.2},
        "steps_until_ready": 4,
    },
}


single_job_args = {}


param_search_args = {
    "search_logging": search_logging,
    "search_resources": search_resources,
    "search_config": search_config,
}


def check_correct_results(experiment_dir: str, api_check: bool = False) -> None:
    """Ensure that correct results and directories were generated."""
    assert os.path.exists(experiment_dir)
    # Check that json config, hyper and meta logs were created
    assert os.path.exists(os.path.join(experiment_dir, "hyper_log.pkl"))
    assert os.path.exists(os.path.join(experiment_dir, "meta_log.hdf5"))
    assert os.path.exists(os.path.join(experiment_dir, "search_base_config.json"))

    # Check that experiment config yaml was created (reproducibility)
    if api_check:
        assert os.path.exists(os.path.join(experiment_dir, "experiment_config.yaml"))


def test_run_pbt() -> None:
    """Test job launch wrapper - Run PDE experiment on local machine."""
    exp_dir = os.path.join(experiment_dir, "run_test")
    meta_job_args["experiment_dir"] = exp_dir
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # run_hyperparameter_search(
    #     resource_to_run, meta_job_args, single_job_args, param_search_args
    # )

    # # Check generated directories for correctness
    # check_correct_results(exp_dir)
