import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Union
import re
from .static_2d_plots import moving_smooth_ts


def visualize_1D_bar(hyper_df: pd.core.frame.DataFrame,
                     param_to_plot: str = "param",
                     target_to_plot: str = "target",
                     plot_title: str = "Temp Title",
                     xy_labels: list = ["x", "y"],
                     every_nth_tick: int = 1,
                     ylims: Union[None, tuple] = None,
                     round_ticks: int = 1,
                     fig = None, ax = None,
                     figsize: tuple=(9, 6),
                     hline: Union[None, float] = None,
                     fixed_params: Union[None, dict]=None):
    """ Plot 1d Bar for single variable and y - select from df. """
    if fig is None or ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Select the data to plot - max. fix 2 other vars
    p_to_plot = [param_to_plot] + [target_to_plot]

    sub_log = hyper_df.hyper_log.copy()
    if fixed_params is not None:
        for k, v in fixed_params.items():
            sub_log = sub_log[sub_log[k].astype(float) == v]

    # Subselect the desired params from the pd df
    temp_df = sub_log[p_to_plot]
    param_array = temp_df[param_to_plot]
    target_array = temp_df[target_to_plot]

    # Plot the data
    plot_1D_bar(param_array, target_array,
                fig, ax, plot_title, xy_labels,
                every_nth_tick, ylims, round_ticks, hline)


def plot_1D_bar(param_array, target_array, fig=None, ax=None,
                plot_title: str = "Temp Title",
                xy_labels: list = ["x", "y"],
                every_nth_tick: int = 1,
                ylims: Union[None, tuple] = None,
                round_ticks: int = 1,
                hline: Union[None, float] = None,
                figsize: tuple=(9, 6)):
    """ Do actual matplotlib plotting task from selected data. """
    if fig is None or ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot the bar data
    xlen = len(param_array)
    ax.bar(np.arange(xlen), target_array)

    # Handle xlabel ticks to set.
    ax.set_xticks(np.arange(0, xlen, every_nth_tick))
    xlabels = [str(round(i, round_ticks)) for j, i
               in enumerate(param_array)
               if j%every_nth_tick == 0]
    ax.set_xticklabels(xlabels)

    # Set axis labels, title and y limits
    ax.set_title(plot_title)
    ax.set_ylabel(xy_labels[1])
    ax.set_xlabel(xy_labels[0])
    if ylims is not None:
        ax.set_ylim(ylims)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add a horizontal line for some baseline level
    if hline is not None:
        ax.axhline(hline, ls="--", c="r", alpha=0.5)
    return fig, ax


def visualize_1D_line(hyper_df: pd.core.frame.DataFrame,
                     param_to_plot: str,
                     target_to_plot: str,
                     plot_title: str = "Temp Title",
                     xy_labels: list = ["x", "y"],
                     every_nth_tick: int = 1,
                     ylims: Union[None, tuple] = None,
                     round_ticks: int = 1,
                     figsize: tuple=(8, 5),
                     hline: Union[None, float] = None,
                     fig=None, ax=None):
    """ Plot a 1d Line w. dots for single var. and its y mapping. """
    if fig is None or ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.plot(hyper_df[param_to_plot], hyper_df[target_to_plot])
    ax.scatter(hyper_df[param_to_plot], hyper_df[target_to_plot],
               zorder=5)

    xlabels = [str(round(i, round_ticks)) for j, i
               in enumerate(hyper_df[param_to_plot])
               if j%every_nth_tick == 0]
    xticks = [hyper_df[param_to_plot].iloc[j] for j, i
               in enumerate(hyper_df[param_to_plot])
               if j%every_nth_tick == 0]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)

    ax.set_title(plot_title)
    ax.set_ylabel(xy_labels[1])
    ax.set_xlabel(xy_labels[0])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    if ylims is not None:
        ax.set_ylim(ylims)

    if hline is not None:
        ax.axhline(hline, ls="--", c="r", alpha=0.5)
    return fig, ax


def plot_1D_line(param_array, target_array, fig=None, ax=None,
                 plot_title: str = "Temp Title",
                 xy_labels: list = ["x", "y"],
                 every_nth_tick: int = 1,
                 ylims: Union[None, tuple] = None,
                 round_ticks: int = 1,
                 hline: Union[None, float] = None,
                 labels: Union[list, None] = None,
                 figsize: tuple=(9, 6)):
    """ Do actual matplotlib plotting task from selected data. """
    if fig is None or ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot the bar data
    if len(target_array.shape) < 2:
        ax.plot(param_array, target_array)
        ax.scatter(param_array, target_array, zorder=5)
    else:
        for i in range(target_array.shape[0]):
            if labels is not None:
                ax.plot(param_array, target_array[i], label=labels[i])
            else:
                ax.plot(param_array, target_array[i])
            ax.scatter(param_array, target_array[i], zorder=5)

    # Handle xlabel ticks to set.
    xlabels = [str(round(i, round_ticks)) for j, i
               in enumerate(param_array)
               if j%every_nth_tick == 0]
    xticks = [param_array[j] for j, i
               in enumerate(param_array)
               if j%every_nth_tick == 0]
    ax.set_xticks(xticks)
    ax.set_xticklabels(xlabels)

    # Set axis labels, title and y limits
    ax.set_title(plot_title)
    ax.set_ylabel(xy_labels[1])
    ax.set_xlabel(xy_labels[0])
    if labels is not None:
        ax.legend()
    if ylims is not None:
        ax.set_ylim(ylims)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Add a horizontal line for some baseline level
    if hline is not None:
        ax.axhline(hline, ls="--", c="r", alpha=0.5)
    return fig, ax


def tokenize(filename):
    """ Helper to sort the log files adequately. """
    digits = re.compile(r'(\d+)')
    return tuple(int(token) if match else token
                 for token, match in
                 ((fragment, digits.search(fragment))
                  for fragment in digits.split(filename)))


def visualize_1D_lcurves(main_log: dict,
                        iter_to_plot: str="num_episodes",
                        target_to_plot: str="ep_reward",
                        smooth_window: int=20,
                        plot_title: str = "Temp Title",
                        xy_labels: list = [r"# Train Iter",
                                         r"Temp Y-Label"],
                        base_label: str="{}",
                        curve_labels: list = [],
                        every_nth_tick: int = 1,
                        plot_std_bar: bool = False,
                        run_ids: Union[None, list] = None,
                        rgb_tuples: Union[List[tuple], None] = None,
                        num_legend_cols: Union[int, None] = 1,
                        fig=None, ax=None, figsize: tuple=(9, 6)):
    """ Plot learning curves from meta_log. Select data and customize plot. """
    if fig is None or ax is None:
        fig, ax = plt.subplots(1, 1, figsize=figsize)

    # Plot all curves if not subselected
    if run_ids is None:
        run_ids = main_log.eval_ids
        run_ids.sort(key=tokenize)

    if len(curve_labels) == 0:
        curve_labels = run_ids

    if rgb_tuples is None:
        # Default colormap is blue to red diverging seaborn palette
        color_by = sns.diverging_palette(240, 10, sep=1, n=len(run_ids))
        #color_by = sns.light_palette("navy", len(run_ids), reverse=False)
    else:
        color_by = rgb_tuples

    for i in range(len(run_ids)):
        label = curve_labels[i]
        run_id = run_ids[i]
        # Smooth the curve to plot for a specified window (1 = no smoothing)
        smooth_mean, _ = moving_smooth_ts(
            main_log[run_id].stats[target_to_plot]["mean"], smooth_window)
        smooth_std, _ = moving_smooth_ts(
            main_log[run_id].stats[target_to_plot]["std"], smooth_window)
        ax.plot(main_log[run_id].time[iter_to_plot]["mean"], smooth_mean,
                 color=color_by[i], label=base_label.format(label))

        if plot_std_bar:
            ax.fill_between(main_log[run_id].time[iter_to_plot]["mean"],
                             smooth_mean-smooth_std, smooth_mean+smooth_std,
                             color=color_by[i], alpha=0.5)

    range_x = main_log[run_id].time[iter_to_plot]["mean"]
    ax.set_xticks(range_x)
    ax.set_xticklabels([str(int(label)) for label in range_x])
    for n, label in enumerate(ax.xaxis.get_ticklabels()):
        if n % every_nth_tick != 0:
            label.set_visible(False)

    ax.legend(fontsize=15, ncol=num_legend_cols)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_title(plot_title)
    ax.set_xlabel(xy_labels[0])
    ax.set_ylabel(xy_labels[1])
    fig.tight_layout()
    return fig, ax
