try:
    import matplotlib
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(f"{err}. You need to install `matplotlib` "
                              "to use the `mle_toolbox.visualize` module.")

try:
    import seaborn
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(f"{err}. You need to install `seaborn` "
                              "to use the `mle_toolbox.visualize` module.")

from .visualize_results_2d import (visualize_2D_grid,
                                   plot_heatmap_array,
                                   moving_smooth_ts)
from .visualize_results_1d import (visualize_1D_lcurves,
                                   visualize_1D_bar,
                                   visualize_1D_line,
                                   plot_1D_bar,
                                   plot_1D_line)


__all__ = [
           'visualize_2D_grid',
           'plot_heatmap_array',
           'moving_smooth_ts'
           'visualize_1D_lcurves',
           'visualize_1D_line',
           'visualize_1D_bar',
           'plot_1D_line',
           'plot_1D_bar'
           ]
