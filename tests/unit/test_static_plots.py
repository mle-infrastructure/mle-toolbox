import os
from mle_toolbox import load_result_logs
from mle_toolbox.visualize import (
    visualize_1D_bar,
    visualize_1D_line,
    visualize_1D_lcurves,
    visualize_2D_grid,
)


def test_1d_bar_static():
    fname = "static_1D_bar.png"
    if os.path.exists(fname):
        os.remove(fname)

    experiment_dir = "tests/unit/fixtures/experiment_1"
    meta_log, hyper_log = load_result_logs(experiment_dir)

    target_to_plot = "integral"
    param_to_plot = "noise_mean"
    fixed_params = {"x_0": 10}

    visualize_1D_bar(
        hyper_log,
        fixed_params,
        param_to_plot,
        target_to_plot,
        plot_title=r"Final State Value - PDE Integration",
        xy_labels=[r"Noise Mean", r"Final Integral"],
        every_nth_tick=1,
        round_ticks=3,
        hline=2,
        fname=fname,
    )

    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)


def test_1d_line_static():
    fname = "static_1D_line.png"
    if os.path.exists(fname):
        os.remove(fname)

    experiment_dir = "tests/unit/fixtures/experiment_1"
    meta_log, hyper_log = load_result_logs(experiment_dir)
    param_to_plot = "noise_mean"
    target_to_plot = "integral"
    fixed_params = {"x_0": 10}
    visualize_1D_line(
        hyper_log,
        fixed_params,
        param_to_plot,
        target_to_plot,
        plot_title=r"Final State Value - PDE Integration",
        xy_labels=[r"Noise Mean", r"Final Integral"],
        every_nth_tick=1,
        round_ticks=3,
        hline=4,
        fname=fname,
    )

    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)


def test_1d_lcurves_static():
    fname = "static_1D_lcurve.png"
    if os.path.exists(fname):
        os.remove(fname)

    experiment_dir = "tests/unit/fixtures/experiment_1"
    meta_log, hyper_log = load_result_logs(experiment_dir)
    visualize_1D_lcurves(
        meta_log,
        iter_to_plot="step_counter",
        target_to_plot="noise",
        smooth_window=3,
        plot_title="Example Plot",
        xy_labels=["# Steps", "Noise"],
        base_label=r"{}",
        curve_labels=[],
        every_nth_tick=3,
        plot_std_bar=True,
        fname=fname,
    )

    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)


def test_2d_grid_static():
    fname = "static_2D_grid.png"
    if os.path.exists(fname):
        os.remove(fname)

    experiment_dir = "tests/unit/fixtures/experiment_1"
    meta_log, hyper_log = load_result_logs(experiment_dir)
    params_to_plot = ["noise_mean", "x_0"]
    target_to_plot = "integral"
    visualize_2D_grid(
        hyper_log,
        {},
        params_to_plot,
        target_to_plot,
        plot_title=r"Final State Value - PDE Integration",
        xy_labels=[r"Noise Mean", r"Init $x_0$"],
        variable_name="Final Integral",
        every_nth_tick=1,
        round_ticks=3,
        text_in_cell=False,
        max_heat=None,
        fname=fname,
    )

    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)
