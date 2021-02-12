import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from typing import List, Union


def moving_smooth_ts(ts, window_size=20):
    """ Smoothes a time series using a moving average filter. """
    smooth_df = pd.DataFrame(ts)
    mean_ts = smooth_df[0].rolling(window_size, min_periods=1).mean()
    std_ts = smooth_df[0].rolling(window_size, min_periods=1).std()
    return mean_ts, std_ts


def visualize_2D_grid(hyper_df: pd.core.frame.DataFrame,
                      fixed_params: Union[None, dict] = None,
                      params_to_plot: list=[],
                      target_to_plot: str="target",
                      plot_title: str = "Temp Title",
                      xy_labels: list = [],
                      variable_name: Union[None, str] = "Var Label",
                      every_nth_tick: int = 1,
                      plot_colorbar: bool = True,
                      text_in_cell: bool = True,
                      max_heat: Union[None, float] = None,
                      min_heat: Union[None, float] = None,
                      norm_cols: bool = False,
                      norm_rows: bool = False,
                      return_array: bool = False,
                      round_ticks: int = 1,
                      figsize: tuple=(10, 8),
                      cmap="magma"):
    """ Fix certain params & visualize grid target value over other two. """
    assert len(params_to_plot) == 2, "You can only plot 2 variables!"

    # Select the data to plot - max. fix 2 other vars
    p_to_plot = params_to_plot + [target_to_plot]
    if fixed_params is not None:
        param_list = list(fixed_params.items())
        fix_param1 = hyper_df[param_list[0][0]] == param_list[0][1]
        fix_param2 = hyper_df[param_list[1][0]] == param_list[1][1]

        # Subselect the desired params from the pd df
        temp_df = hyper_df[fix_param1 & fix_param2][p_to_plot]
    else:
        temp_df = hyper_df[p_to_plot]

    # Construct the 2D array using helper function
    range_x = np.unique(temp_df[p_to_plot[0]])
    range_y = np.unique(temp_df[p_to_plot[1]])

    heat_array = get_heatmap_array(range_x, range_y, temp_df.to_numpy(),
                                   norm_cols, norm_rows)

    if return_array:
        return heat_array
    else:
        # Construct the plot
        fig, ax = plot_heatmap_array(range_x, range_y, heat_array, plot_title,
                                     xy_labels, variable_name, every_nth_tick,
                                     plot_colorbar, text_in_cell, max_heat,
                                     min_heat, round_ticks, figsize=figsize,
                                     cmap=cmap)
        return fig, ax


def get_heatmap_array(range_x: np.ndarray,
                      range_y: np.ndarray,
                      results_df: np.ndarray,
                      norm_cols: bool = False,
                      norm_rows: bool = False):
    """ Construct the 2D array to plot the heat. """
    bring_the_heat = np.zeros((len(range_y), len(range_x)))
    for i, val_x in enumerate(range_x):
        for j, val_y in enumerate(range_y):
            case_at_hand = np.where((results_df[:, 0] == val_x) & (results_df[:, 1] == val_y))
            results_temp = results_df[case_at_hand, 2]
            # Reverse index so that small in bottom left corner
            bring_the_heat[len(range_y)-1 - j, i] = results_temp

    # Normalize the rows and/or columns by the maximum
    if norm_cols:
        bring_the_heat /=  bring_the_heat.max(axis=0)
    if norm_rows:
        bring_the_heat /=  bring_the_heat.max(axis=1)[:,np.newaxis]
    return bring_the_heat


def plot_heatmap_array(range_x: np.ndarray,
                       range_y: np.ndarray,
                       heat_array: np.ndarray,
                       title: str,
                       xy_labels: list,
                       variable_name: Union[None, str],
                       every_nth_tick: int,
                       plot_colorbar: bool = True,
                       text_in_cell: bool = True,
                       max_heat: Union[None, float] = None,
                       min_heat: Union[None, float] = None,
                       round_ticks: int=1,
                       fig = None,
                       ax = None,
                       figsize: tuple=(10, 8),
                       cmap = "magma"):
    """ Plot the 2D heatmap. """
    if fig is None or ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    if max_heat is None and min_heat is None:
        im = ax.imshow(heat_array, cmap=cmap, vmax=np.max(heat_array),
                       vmin=np.min(heat_array))
    elif max_heat is not None and min_heat is None:
        im = ax.imshow(heat_array, cmap=cmap, vmax=max_heat)
    elif max_heat is None and min_heat is not None:
        im = ax.imshow(heat_array, cmap=cmap, vmin=min_heat)
    else:
        im = ax.imshow(heat_array, cmap=cmap, vmin=min_heat, vmax=max_heat)

    ax.set_yticks(np.arange(len(range_y)))
    if len(range_y) != 0:
        if type(range_y[-1]) is not str:
            if round_ticks != 0:
                yticklabels = [str(round(float(label), round_ticks))
                               for label in range_y[::-1]]
            else:
                yticklabels = [str(int(label)) for label in range_y[::-1]]
        else:
            yticklabels = [str(label) for label in range_y[::-1]]
    else:
        yticklabels = []
    ax.set_yticklabels(yticklabels)

    for n, label in enumerate(ax.yaxis.get_ticklabels()):
        if n % every_nth_tick != 0:
            label.set_visible(False)


    ax.set_xticks(np.arange(len(range_x)))
    if len(range_x) != 0:
        if type(range_x[-1]) is not str:
            if round_ticks != 0:
                xticklabels = [str(round(float(label), round_ticks))
                               for label in range_x]
            else:
                xticklabels = [str(int(label))
                               for label in range_x]
        else:
            xticklabels = [str(label) for label in range_x]
    else:
        xticklabels = []
    ax.set_xticklabels(xticklabels)

    for n, label in enumerate(ax.xaxis.get_ticklabels()):
        if n % every_nth_tick != 0:
            label.set_visible(False)


    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    ax.set_title(title)
    if len(range_x) != 0:
        ax.set_xlabel(xy_labels[0])
    if len(range_y) != 0:
        ax.set_ylabel(xy_labels[1])


    if plot_colorbar:
        # fig.subplots_adjust(right=0.8)
        # cbar_ax = fig.add_axes([0.85, 0.25, 0.05, 0.5])
        # cbar = fig.colorbar(im, cax=cbar_ax)
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="7%", pad=0.15)
        cbar = fig.colorbar(im, cax=cax)
        if variable_name is not None:
            cbar.set_label(variable_name, rotation=270, labelpad=30)
        fig.tight_layout()

    if text_in_cell:
        for y in range(heat_array.shape[0]):
            for x in range(heat_array.shape[1]):
                ax.text(x , y , '%.2f' % heat_array[y, x],
                         horizontalalignment='center',
                         verticalalignment='center',)
    return fig, ax
