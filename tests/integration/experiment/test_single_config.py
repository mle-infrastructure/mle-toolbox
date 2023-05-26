import unittest
import os
import shutil
import subprocess as sp
from mle_toolbox.launch.single_config import run_single_config


resource_to_run = "local"
job_filename = "examples/toy_single_objective/train.py"
config_filename = "examples/toy_single_objective/base_config_1.yaml"
experiment_dir = "examples/experiments/single"


def check_correct_results(experiment_dir: str, api_check: bool = False) -> None:
    """Ensure that correct results and directories were generated."""
    base_str = os.path.split(config_filename)[1].split(".")[0]
    dir_to_check = os.path.join(experiment_dir, base_str + "/")

    # Check that experiment directory with results exists
    assert os.path.exists(dir_to_check)
    # Check that copied .json config exists
    assert os.path.exists(os.path.join(dir_to_check, os.path.split(config_filename)[1]))
    # Check that log file exists
    assert os.path.exists(os.path.join(dir_to_check, "logs", "log_seed_0.hdf5"))
    # Check that figure file exists
    assert os.path.exists(os.path.join(dir_to_check, "figures/fig_1_seed_0.png"))

    # Check that experiment config yaml was created (reproducibility)
    if api_check:
        assert os.path.exists(os.path.join(experiment_dir, "experiment_config.yaml"))


def test_run_single() -> None:
    """Test job launch wrapper - Run PDE experiment on local machine."""
    exp_dir = os.path.join(experiment_dir, "run_test")
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute single config wrapper function
    run_single_config(
        resource_to_run,
        meta_job_args={
            "base_train_fname": job_filename,
            "base_train_config": config_filename,
            "experiment_dir": exp_dir,
        },
        single_job_args={},
    )

    # Check generated directories for correctness
    check_correct_results(exp_dir)


def test_api_single() -> None:
    """Execute `mle run pde_single.yaml` and check running pipeline."""
    os.chdir("./examples")
    exp_dir = "experiments/single/api_test"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = (
        "mle run toy_single_objective/mle_single_config.yaml -nw -np -resource local"
        f" --experiment_dir {exp_dir}"
    )

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    check_correct_results(exp_dir, api_check=True)
    os.chdir("..")


if __name__ == "__main__":
    unittest.main()
