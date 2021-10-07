import os
import shutil
import subprocess as sp
from mle_toolbox.launch.search_experiment import run_hyperparameter_search


resource_to_run = "local"
experiment_dir = "examples/experiments/smbo"
meta_job_args = {"base_train_fname": "examples/numpy_pde/run_pde_int.py",
                 "base_train_config": "examples/numpy_pde/pde_int_config_1.json"}

search_logging = {"reload_log": False,
                  "verbose_log": True,
                  "max_objective": True,
                  "aggregate_seeds": "p50",
                  "problem_type": "final",
                  "eval_metrics": ["integral", "noise"]}

search_resources_sync = {"num_search_batches": 3,
                         "num_evals_per_batch": 2,
                         "num_seeds_per_eval": 2,
                         "random_seeds": [1, 4]}

search_config = {
    "search_type": "smbo",
    "search_schedule": "sync",
    "search_params": {
        "real": {"x_0": {"begin": 1,
                         "end": 10,
                         "prior": "log_uniform"},
                 "noise_mean": {"begin": 0,
                                "end": 0.01,
                                "prior": "uniform"}
                 }
    },
    "search_config": {
        "metric_to_model": "integral",     # Which of the eval metrics to model
        "base_estimator": "GP",            # "GP", "RF", "ET", "GBRT"
        "acq_function": "gp_hedge",        # "LCB", "EI", "PI", "gp_hedge" (samples)
        "n_initial_points": 1              # Init points >= than batch size!
    }
}

single_job_args = {}


def check_correct_results(experiment_dir: str,
                          api_check: bool = False) -> None:
    """ Ensure that correct results and directories were generated. """
    assert os.path.exists(experiment_dir)
    # Check that json config, hyper and meta logs were created
    assert os.path.exists(os.path.join(experiment_dir, "hyper_log.pkl"))
    assert os.path.exists(os.path.join(experiment_dir, "meta_log.hdf5"))
    assert os.path.exists(os.path.join(experiment_dir, "search_base_config.json"))

    # Check that experiment config yaml was created (reproducibility)
    if api_check:
        assert os.path.exists(os.path.join(experiment_dir, "experiment_config.yaml"))


def test_run_smbo() -> None:
    """ Test job launch wrapper - Run PDE experiment on local machine. """
    exp_dir = os.path.join(experiment_dir, "run_test")
    meta_job_args["experiment_dir"] = exp_dir
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    param_search_args = {"search_logging": search_logging,
                         "search_resources": search_resources_sync,
                         "search_config": search_config}

    run_hyperparameter_search(
        resource_to_run,
        meta_job_args,
        single_job_args,
        param_search_args)

    # Check generated directories for correctness
    check_correct_results(exp_dir)


def test_api_smbo() -> None:
    """ Execute `mle run pde_grid_sync.yaml` and check running pipeline. """
    os.chdir('./examples')
    exp_dir = "experiments/smbo/api_test"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = ("mle run numpy_pde/pde_search_smbo.yaml -nw -np -resource local"
                   f" --experiment_dir {exp_dir}")

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    check_correct_results(exp_dir, api_check=True)
    os.chdir('..')
