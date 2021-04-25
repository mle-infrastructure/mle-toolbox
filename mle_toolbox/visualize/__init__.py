try:
    import matplotlib
    # Suppress all axis/future warnings from mpl
    import warnings
    warnings.filterwarnings("ignore", module="matplotlib\..*")
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(f"{err}. You need to install `matplotlib` "
                              "to use the `mle_toolbox.visualize` module.")

try:
    import seaborn as sns
    # Set overall plots appearance sns style
    sns.set(context='poster', style='white', palette='Paired',
            font='sans-serif', font_scale=1.05, color_codes=True, rc=None)
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(f"{err}. You need to install `seaborn` "
                              "to use the `mle_toolbox.visualize` module.")


# Static plots of results
from .static_2d_plots import (visualize_2D_grid,
                              plot_2D_heatmap,
                              moving_smooth_ts)
from .static_1d_plots import (visualize_1D_lcurves,
                              visualize_1D_bar,
                              visualize_1D_line,
                              plot_1D_bar,
                              plot_1D_line)

# Dynamics animations of results
from .dynamic_1d_anims import animate_1D_lines
from .dynamic_2d_grid import animate_2D_grid
from .dynamic_2d_scatter import animate_2D_scatter


__all__ = [
           'visualize_2D_grid',
           'plot_heatmap_array',
           'moving_smooth_ts'
           'visualize_1D_lcurves',
           'visualize_1D_line',
           'visualize_1D_bar',
           'plot_1D_line',
           'plot_1D_bar',
           'animate_1D_lines',
           'animate_2D_grid',
           'animate_2D_scatter'
           ]
