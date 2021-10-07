import os
import shutil
import subprocess as sp
from mle_toolbox.launch.search_experiment import run_hyperparameter_search


resource_to_run = "local"
experiment_dir = "examples/experiments/nevergrad"
meta_job_args = {"base_train_fname": "examples/toy_multiobj/run_toy.py",
                 "base_train_config": "examples/toy_multiobj/toy_config.yaml"}

search_logging = {"max_objective": False,
                  "eval_metrics": ["objective_1", "objective_2"]}

search_resources_sync = {"num_search_batches": 3,
                         "num_evals_per_batch": 3,
                         "num_seeds_per_eval": 1}

search_config = {
    "search_type": "nevergrad",
    "search_params": {
        "real": {"lrate": {"begin": 0.01,
                           "end": 0.5,
                           "prior": "log_uniform"}},
        "categorical": {"architecture": ["cnn", "mlp"]},
        "integer": {"batch_size": {"begin": 1,
                                   "end": 10,
                                   "prior": "uniform"}},
    },
    "search_config": {"optimizer": "CMA"}
}

single_job_args = {}


def check_correct_results(experiment_dir: str,
                          api_check: bool = False) -> None:
    """ Ensure that correct results and directories were generated. """
    assert os.path.exists(experiment_dir)
    # Check that json config, hyper and meta logs were created
    assert os.path.exists(os.path.join(experiment_dir, "hyper_log.pkl"))
    assert os.path.exists(os.path.join(experiment_dir, "meta_log.hdf5"))
    assert os.path.exists(os.path.join(experiment_dir, "search_base_config.yaml"))

    # Check that experiment config yaml was created (reproducibility)
    if api_check:
        assert os.path.exists(os.path.join(experiment_dir, "experiment_config.yaml"))


def test_run_nevergrad() -> None:
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


def test_api_nevergrad() -> None:
    """ Execute `mle run pde_grid_sync.yaml` and check running pipeline. """
    os.chdir('./examples')
    exp_dir = "experiments/nevergrad/api_test"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = ("mle run toy_multiobj/toy_nevergrad.yaml -nw -np -resource local"
                   f" --experiment_dir {exp_dir}")

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    check_correct_results(exp_dir, api_check=True)
    os.chdir('..')
