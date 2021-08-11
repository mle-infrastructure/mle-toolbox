import os
from os import listdir
from os.path import isfile, join
import shutil
import subprocess as sp


def check_correct_results(experiment_dir: str) -> None:
    """ Ensure that correct results and directories were generated. """
    assert os.path.exists(experiment_dir)
    # Check that figures and report files were correctly generated
    assert os.path.exists(os.path.join(experiment_dir, "figures/integral_1d.png"))
    assert os.path.exists(os.path.join(experiment_dir, "figures/noise_1d.png"))
    assert os.path.exists(os.path.join(experiment_dir, "figures/integral_x_0_noise_mean_2d.png"))
    assert os.path.exists(os.path.join(experiment_dir, "figures/noise_x_0_noise_mean_2d.png"))

    report_path = os.path.join(experiment_dir, "reports")
    assert os.path.exists(report_path)
    onlyfiles = [f for f in listdir(report_path) if isfile(join(report_path, f))]
    assert len([f for f in onlyfiles if f.endswith(".md")]) == 1
    assert len([f for f in onlyfiles if f.endswith(".html")]) == 1
    assert len([f for f in onlyfiles if f.endswith(".pdf")]) == 1


def test_api_report() -> None:
    """ Execute `mle run pde_grid_sync.yaml` and check running pipeline. """
    os.chdir('./examples')
    exp_dir = "experiments/report/"
    # Remove experiment dir at start of test
    if os.path.exists(exp_dir) and os.path.isdir(exp_dir):
        shutil.rmtree(exp_dir)

    # Execute the mle api command
    bashCommand = ("mle run numpy_pde/pde_search_grid_sync.yaml -nw -resource local"
                   f" --experiment_dir {exp_dir}"
                   f" --purpose Test report generation")

    process = sp.Popen(bashCommand.split(), stdout=sp.PIPE)
    output, error = process.communicate()

    # Check generated directories for correctness
    check_correct_results(exp_dir)
    os.chdir('..')