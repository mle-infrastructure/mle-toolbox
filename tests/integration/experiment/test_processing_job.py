import os
import shutil
import subprocess as sp
from mle_toolbox.launch.processing_job import run_processing_job


experiment_dir = "examples/experiments/processing/"
resource_to_run = "local"
processing_args = {"processing_fname": "tests/unit/fixtures/python_script.py",
                   "processing_job_args": {},
                   "extra_cmd_line_input": {"figures_dir": "figures"}}


def check_correct_results(experiment_dir: str,
                          api_check: bool = False) -> None:
    """ Ensure that correct results and directories were generated. """
    assert os.path.exists(experiment_dir)
    plot_path = os.path.join(experiment_dir, "figures/sine_wave.png")
    assert os.path.exists(plot_path)


def test_run_processing() -> None:
    """ Test job launch wrapper - Run PDE experiment on local machine. """
    # Remove experiment dir at start of test
    if os.path.exists(experiment_dir) and os.path.isdir(experiment_dir):
        shutil.rmtree(experiment_dir)
    run_processing_job(resource_to_run,
                       processing_args,
                       experiment_dir)
    check_correct_results(experiment_dir)


# def test_api_processing() -> None:
#     """ Execute `mle run pde_grid_sync.yaml` and check running pipeline. """
#     os.chdir('./examples')
#     exp_dir = "experiments/processing/pre_post_api"
#     # Remove experiment dir at start of test
#     if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
#         shutil.rmtree(exp_dir)
#
#     # Execute the mle api command
#     bashCommand = ("mle run numpy_pde/pde_search_grid_sync.yaml -nw -np -resource local"
#                    f" --experiment_dir {exp_dir}")
#
#     process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
#     output, error = process.communicate()
#
#     # Check generated directories for correctness
#     check_correct_results(exp_dir, api_check=True)
#     os.chdir('..')
