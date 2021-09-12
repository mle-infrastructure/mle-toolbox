import os
import numpy as np
from mle_toolbox.visualize import (animate_1D_lines,
                                   animate_2D_grid,
                                   animate_2D_scatter,
                                   animate_3D_scatter,
                                   animate_3D_surface)


def test_1d_line():
    fname = "line_anim.gif"
    if os.path.exists(fname):
        os.remove(fname)
    time_steps = 50
    num_lines = 2
    noisy_lines = np.random.normal(size=(time_steps, num_lines))
    animate_1D_lines(noisy_lines, dt=1, line_labels=[5, 6], base_label="Line",
                     ylabel="Value", xlabel="Time",
                     title="Animated Random Numbers", interval=100, fps=10,
                     fname=fname, direct_save=True)
    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)


def test_2d_grid():
    fname = "grid_anim.gif"
    if os.path.exists(fname):
        os.remove(fname)
    time_steps = 50
    grid_size = 10
    noisy_grid = np.random.normal(size=(time_steps, grid_size, grid_size))
    animate_2D_grid(noisy_grid, var_name="A Variable", dt=1,
                    ylabel="Cool variable", xlabel="Not so cool variable",
                    range_y=None, range_x=None, every_nth=1, round_ticks=2,
                    vmin=None, vmax=None,
                    title="A Grid Title", interval=100, fps=60,
                    fname=fname, direct_save=True)
    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)


def test_2d_scatter():
    fname = "scatter_2D_anim.gif"
    if os.path.exists(fname):
        os.remove(fname)
    time_steps = 50
    num_points = 10
    num_coords = 2
    noisy_points = np.random.normal(size=(time_steps, num_points, num_coords))
    animate_2D_scatter(noisy_points, dt=1,
                       ylabel="Cool variable", xlabel="Not so cool variable",
                       title="Animated Title", no_axis=False,
                       interval=100, fps=60,
                       fname=fname, direct_save=True)
    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)


def test_3d_scatter():
    fname = "scatter_3D_anim.gif"
    if os.path.exists(fname):
        os.remove(fname)
    time_steps = 50
    num_points = 10
    num_coords = 3
    noisy_points = np.random.rand(time_steps, num_points, num_coords) * 10
    animate_3D_scatter(noisy_points, dt=1,
                       ylabel="Cool variable",
                       xlabel="Not so cool variable",
                       zlabel="Coolest variable",
                       title="Animated Title", no_axis=False,
                       interval=100, fps=60,
                       fname=fname)
    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)


def test_3d_surface():
    fname = "surface_3D_anim.gif"
    if os.path.exists(fname):
        os.remove(fname)
    N = 250   # Meshsize
    fps = 10  # frame per sec
    frn = 20  # frame number of the animation

    x = np.linspace(-4, 4, N + 1)
    x, y = np.meshgrid(x, x)
    surface = np.zeros((frn, N + 1, N + 1))

    f = lambda x,y,sig : 1 / np.sqrt(sig) * np.exp(-(x**2 + y**2) / sig**2)

    for i in range(frn):
        surface[i, :, :] = f(x, y, 1.5 + np.sin(i * 2 * np.pi / frn))

    animate_3D_surface(x, y, surface, fname=fname)
    assert os.path.exists(fname)
    if os.path.exists(fname):
        os.remove(fname)
