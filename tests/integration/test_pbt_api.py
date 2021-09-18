import os
import shutil
import subprocess as sp
from mle_toolbox.launch.pbt_experiment import run_population_based_training


resource_to_run = "local"
experiment_dir = "examples/experiments/pbt"
meta_job_args = {"base_train_fname": "examples/pbt_quadratic/run_quadratic_steps.py",
                 "base_train_config": "examples/pbt_quadratic/quadratic_config.json"}

pbt_logging = {"max_objective": True,
               "eval_metric": "objective"}

pbt_resources = {"num_population_members": 2,
                 "num_total_update_steps": 8,
                 "num_steps_until_ready": 4,
                 "num_steps_until_eval": 4}

pbt_config = {
    "pbt_params": {
        "real": {
            "h0": {
                "begin": 0,
                "end": 1,
                "init": [0.1, 0.9]
            },
            "h1": {
                "begin": 0,
                "end": 1,
                "init": [0.9, 0.1]
            }
        }
    },
    "exploration": {
        "strategy": "perturb"
    },
    "selection": {
        "strategy": "binary_tournament"
    }
}

pbt_args = {"pbt_logging": pbt_logging,
            "pbt_resources": pbt_resources,
            "pbt_config": pbt_config}
single_job_args = {}


def check_correct_results(experiment_dir: str,
                          api_check: bool = False) -> None:
    """ Ensure that correct results and directories were generated. """
    assert os.path.exists(experiment_dir)
    # Check that json config, hyper and meta logs were created
    assert os.path.exists(os.path.join(experiment_dir, "pbt_log.pkl"))
    # assert os.path.exists(os.path.join(experiment_dir, "worker_log.hdf5"))
    assert os.path.exists(os.path.join(experiment_dir, "pbt_base_config.json"))

    # Check that experiment config yaml was created (reproducibility)
    if api_check:
        assert os.path.exists(os.path.join(experiment_dir, "experiment_config.yaml"))


def test_api_pbt() -> None:
    """ Execute `mle run pde_grid_sync.yaml` and check running pipeline. """
    os.chdir('./examples')
    exp_dir = "experiments/pbt/api_test"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = ("mle run pbt_quadratic/quadratic_pbt.yaml"
                   " -nw -np -resource local"
                   f" --experiment_dir {exp_dir}")

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    check_correct_results(exp_dir, api_check=True)
    os.chdir('..')

    #mle run pbt_quadratic/quadratic_pbt.yaml -nw -np -resource local --experiment_dir experiments/pbt/api_test
