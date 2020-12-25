import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import List, Union

sns.set(context='poster', style='white', palette='Paired',
        font='sans-serif', font_scale=1.05, color_codes=True, rc=None)


def visualize_1D_bar(hyper_df: pd.core.frame.DataFrame,
                     param_to_plot: str,
                     target_to_plot: str,
                     plot_title: str = "Temp Title",
                     xy_labels: list = ["x", "y"],
                     every_nth_tick: int = 1,
                     ylims: Union[None, tuple] = None,
                     round_ticks: int = 1,
                     figsize: tuple=(9, 6),
                     hline: Union[None, float] = None):
    """ Plot a 1d Bar for a single variable and its y mapping. """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    xlen = len(hyper_df[param_to_plot])
    ax.bar(np.arange(xlen), hyper_df[target_to_plot])
    ax.set_xticks(np.arange(0, xlen, every_nth_tick))
    xlabels = [str(round(i, round_ticks)) for j, i
               in enumerate(hyper_df[param_to_plot])
               if j%every_nth_tick == 0]
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


def visualize_1D_line(hyper_df: pd.core.frame.DataFrame,
                     param_to_plot: str,
                     target_to_plot: str,
                     plot_title: str = "Temp Title",
                     xy_labels: list = ["x", "y"],
                     every_nth_tick: int = 1,
                     ylims: Union[None, tuple] = None,
                     round_ticks: int = 1,
                     figsize: tuple=(8, 5),
                     hline: Union[None, float] = None):
    """ Plot a 1d Line w. dots for single var. and its y mapping. """
    fig, ax = plt.subplots(1, 1, figsize=figsize)
    ax.plot(hyper_df[param_to_plot], hyper_df[target_to_plot])
    ax.scatter(hyper_df[param_to_plot], hyper_df[target_to_plot],
               zorder=5)

    xlabels = [str(round(i, round_ticks)) for j, i
               in enumerate(hyper_df[param_to_plot])
               if j%every_nth_tick == 0]
    xticks = [hyper_df[param_to_plot][j] for j, i
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
