import os
import shutil
from mle_toolbox.launch.processing_job import run_processing_job


experiment_dir = "examples/experiments/processing/"
resource_to_run = "local"
processing_args = {
    "processing_fname": "tests/unit/fixtures/python_script.py",
    "processing_job_args": {},
    "extra_cmd_line_input": {"figures_dir": "figures"},
}


def check_correct_results(experiment_dir: str, api_check: bool = False) -> None:
    """Ensure that correct results and directories were generated."""
    assert os.path.exists(experiment_dir)
    plot_path = os.path.join(experiment_dir, "figures/sine_wave.png")
    assert os.path.exists(plot_path)


def test_run_processing() -> None:
    """Test job launch wrapper - Run PDE experiment on local machine."""
    # Remove experiment dir at start of test
    if os.path.exists(experiment_dir) and os.path.isdir(experiment_dir):
        shutil.rmtree(experiment_dir)
    run_processing_job(resource_to_run, processing_args, experiment_dir)
    check_correct_results(experiment_dir)
