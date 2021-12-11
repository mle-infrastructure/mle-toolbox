import os
import shutil
import glob
import subprocess as sp
from mle_toolbox.launch.multi_config import run_multiple_configs


resource_to_run = "local"
job_filename = "examples/toy_single_objective/train.py"
config_filenames = [
    "examples/toy_single_objective/base_config_1.yaml",
    "examples/toy_single_objective/base_config_2.yaml",
]
job_arguments = {}
num_seeds = num_configs = 2
random_seeds = [2, 3]
experiment_dir = "examples/experiments/multi"


def check_correct_results(
    experiment_dir: str, config_filename: str, api_check: bool = False
) -> None:
    """Ensure that correct results and directories were generated."""
    base_str = os.path.split(config_filename)[1].split(".")[0]
    dir_to_check = os.path.join(experiment_dir, base_str + "/")

    # Check that experiment directory with results exists
    assert os.path.exists(dir_to_check), "Directory missing"
    # Check that copied .json config exists
    json_path = os.path.join(dir_to_check, os.path.split(config_filename)[1])
    assert os.path.exists(json_path), f".json missing: {json_path}"
    # Check that log file exists
    assert os.path.exists(os.path.join(dir_to_check, "logs", "log.hdf5")), "Log missing"
    # Check that figure files exist
    png_counter = len(glob.glob1(os.path.join(dir_to_check, "figures/"), "*.png"))

    assert png_counter == num_seeds, "Figure missing"

    # Check that experiment config yaml was created (reproducibility)
    if api_check:
        assert os.path.exists(
            os.path.join(experiment_dir, "experiment_config.yaml")
        ), "Experiment .yaml missing"


def test_run_multi() -> None:
    """Test multi config job launch wrapper - Run PDE experiment on local machine."""
    exp_dir = os.path.join(experiment_dir, "run_test")
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    run_multiple_configs(
        resource_to_run,
        meta_job_args={"base_train_fname": job_filename, "experiment_dir": exp_dir},
        single_job_args={},
        multi_config_args={
            "config_fnames": config_filenames,
            "num_seeds": num_seeds,
            "random_seeds": random_seeds,
        },
    )

    # Check that all results for different configs were generated
    for cfname in config_filenames:
        check_correct_results(exp_dir, cfname)


def test_api_multi() -> None:
    """Execute `mle run pde_multi.yaml` and check running pipeline."""
    os.chdir("./examples")
    exp_dir = "experiments/multi/api_test"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = (
        "mle run toy_single_objective/mle_multi_config.yaml -nw -np -resource local"
        f" --experiment_dir {exp_dir}"
    )

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    for cfname in config_filenames:
        check_correct_results(exp_dir, cfname, api_check=True)
    os.chdir("..")
