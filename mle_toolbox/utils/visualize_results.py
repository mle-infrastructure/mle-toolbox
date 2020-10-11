import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Union
from .general import mean_over_evals
import re

sns.set(context='poster', style='white', palette='Paired',
        font='sans-serif', font_scale=1, color_codes=True, rc=None)

digits = re.compile(r'(\d+)')
def tokenize(filename):
    """ Helper to sort the log files adequately. """
    return tuple(int(token) if match else token
                 for token, match in
                 ((fragment, digits.search(fragment))
                  for fragment in digits.split(filename)))


def moving_smooth_ts(ts, window_size=20):
    """ Smoothes a time series using a moving average filter. """
    smooth_df = pd.DataFrame(ts)
    mean_ts = smooth_df[0].rolling(window_size, min_periods=1).mean()
    std_ts = smooth_df[0].rolling(window_size, min_periods=1).std()
    return mean_ts, std_ts


def visualize_2D_grid(hyper_df: pd.core.frame.DataFrame,
                      fixed_params: Union[None, dict],
                      params_to_plot: list,
                      target_to_plot: str,
                      plot_title: str = "Temp Title",
                      xy_labels: list = [],
                      variable_name: str = [],
                      every_nth_tick: int = 1,
                      plot_colorbar: bool = True,
                      text_in_cell: bool = True,
                      max_heat: Union[None, float] = None,
                      min_heat: Union[None, float] = None,
                      return_array: bool = False):
    """ Fix certain params & visualize grid target value over other two. """
    assert len(params_to_plot) == 2
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

    heat_array = get_heatmap_array(range_x, range_y, temp_df.to_numpy())

    if return_array:
        return heat_array
    else:
        # Construct the plot
        fig, ax = plot_heatmap_array(range_x, range_y, heat_array, plot_title,
                                     xy_labels, variable_name, every_nth_tick, plot_colorbar,
                                     text_in_cell, max_heat, min_heat)
        return fig, ax


def get_heatmap_array(range_x: np.ndarray,
                      range_y: np.ndarray,
                      results_df: pd.core.frame.DataFrame):
    """ Construct the 2D array to plot the heat. """
    bring_the_heat = np.zeros((len(range_y), len(range_x)))
    for i, val_x in enumerate(range_x):
        for j, val_y in enumerate(range_y):
            case_at_hand = np.where((results_df[:, 0] == val_x) & (results_df[:, 1] == val_y))
            results_temp = results_df[case_at_hand, 2]
            # Reverse index so that small in bottom left corner
            bring_the_heat[len(range_y)-1 - j, i] = results_temp
    #print(bring_the_heat.shape)
    return bring_the_heat


def plot_heatmap_array(range_x: np.ndarray,
                       range_y: np.ndarray,
                       heat_array: np.ndarray,
                       title: str,
                       xy_labels: list,
                       variable_name: str,
                       every_nth_tick: int,
                       plot_colorbar: bool = True,
                       text_in_cell: bool = True,
                       max_heat: Union[None, float] = None,
                       min_heat: Union[None, float] = None):
    """ Plot the 2D heatmap. """
    fig, ax = plt.subplots(figsize=(10, 8))
    cmap = "magma"
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
    ax.set_yticklabels([str(round(float(label), 1)) for label in range_y[::-1]])

    for n, label in enumerate(ax.yaxis.get_ticklabels()):
        if n % every_nth_tick != 0:
            label.set_visible(False)


    ax.set_xticks(np.arange(len(range_x)))
    ax.set_xticklabels([str(round(float(label), 1)) for label in range_x])
    for n, label in enumerate(ax.xaxis.get_ticklabels()):
        if n % every_nth_tick != 0:
            label.set_visible(False)


    # Rotate the tick labels and set their alignment.
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    ax.set_title(title, fontsize=25)
    ax.set_xlabel(xy_labels[0], fontsize=20)
    ax.set_ylabel(xy_labels[1], fontsize=20)

    if plot_colorbar:
        fig.tight_layout()
        fig.subplots_adjust(right=0.8)
        cbar_ax = fig.add_axes([0.85, 0.25, 0.05, 0.5])
        cbar = fig.colorbar(im, cax=cbar_ax)
        #cbar.set_label(variable_name, rotation=270, fontsize=10)

    if text_in_cell:
        for y in range(heat_array.shape[0]):
            for x in range(heat_array.shape[1]):
                ax.text(x , y , '%.2f' % heat_array[y, x],
                         horizontalalignment='center',
                         verticalalignment='center',)
    return fig, ax


def visualize_target_performance_bar():
    """ Implement a bar plot of target performance in hyperdf. """
    raise NotImplementedError


def visualize_learning_curves(main_log: dict,
                              iter_to_plot: str="num_episodes",
                              target_to_plot: str="ep_reward",
                              smooth_window: int=20,
                              plot_title: str = "Temp Title",
                              xy_labels: list = [r"# Train Iter",
                                                 r"Temp Y-Label"],
                              base_label: str="",
                              curve_labels: list = [],
                              every_nth_tick: int = 1,
                              plot_std_bar: bool = False,
                              run_ids: list = None):
    """ Plot learning curves from meta_log. """
    # Plot all curves if not subselected
    if run_ids is None:
        run_ids = list(main_log.keys())
        run_ids.sort(key=tokenize)
    
    if len(curve_labels) == 0:
        curve_labels = run_ids

    fig, axs = plt.subplots(1, 1, figsize=(8, 5))
    color_by = sns.light_palette("navy", len(run_ids), reverse=False)

    for i in range(len(run_ids)):
        label = curve_labels[i]
        run_id = run_ids[i]
        # Smooth the curve to plot
        smooth_mean, _ = moving_smooth_ts(main_log[run_id][target_to_plot]["mean"], smooth_window)
        smooth_std, _ = moving_smooth_ts(main_log[run_id][target_to_plot]["std"], smooth_window)
        axs.plot(main_log[run_id][iter_to_plot]["mean"], smooth_mean,
                 color=color_by[i], label=base_label + " {}".format(label))

        if plot_std_bar:
            axs.fill_between(main_log[run_id][iter_to_plot]["mean"],
                             smooth_mean-smooth_std, smooth_mean+smooth_std, color=color_by[i], alpha=0.5)

    range_x = main_log[run_id][iter_to_plot]["mean"]
    axs.set_xticks(range_x)
    axs.set_xticklabels([str(int(label)) for label in range_x])
    for n, label in enumerate(axs.xaxis.get_ticklabels()):
        if n % every_nth_tick != 0:
            label.set_visible(False)

    axs.legend(fontsize=15)

    axs.spines['top'].set_visible(False)
    axs.spines['right'].set_visible(False)
    axs.set_title(plot_title)
    axs.set_xlabel(xy_labels[0])
    axs.set_ylabel(xy_labels[1])
    fig.tight_layout()
    return fig, axs
