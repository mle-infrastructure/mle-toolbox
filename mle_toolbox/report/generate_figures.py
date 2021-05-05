import os, itertools
from mle_toolbox import load_result_logs
from mle_toolbox.visualize import visualize_1D_lcurves, visualize_2D_grid


class FigureGenerator():
    """ Figure generator class on top of data in meta-log/hyper-log. """
    def __init__(self, experiment_dir: str,
                 meta_log_fname: str = "meta_log.hdf5",
                 hyper_log_fname: str = "hyper_log.pkl",
                 dpi: int = 300):
        self.experiment_dir = experiment_dir
        self.meta_log_fname = meta_log_fname
        self.hyper_log_fname = hyper_log_fname

        # Load in both meta and hyper log
        self.meta_log, self.hyper_log = load_result_logs(experiment_dir,
                                                         meta_log_fname,
                                                         hyper_log_fname)

        # Create a directory for the figures to be generated
        self.figures_dir = os.path.join(experiment_dir, "figures")
        if not os.path.exists(self.figures_dir):
            try: os.makedirs(self.figures_dir)
            except: pass

        # Set default settings for all plots (resolution, etc.)
        self.dpi = dpi

    def generate_1D_figure(self, time_to_plot, stat_to_plot):
        """ Generate and save 1D line/curve figure. """
        # Generate the 1D line plot
        fig, ax = visualize_1D_lcurves(self.meta_log,
                                       iter_to_plot=time_to_plot,
                                       target_to_plot=stat_to_plot,
                                       smooth_window=1,
                                       plot_title=stat_to_plot,
                                       xy_labels = [time_to_plot,
                                                    stat_to_plot],
                                       base_label=r"{}",
                                       curve_labels=[],
                                       every_nth_tick= 5,
                                       plot_std_bar= True)
        ax.legend(ncol=4, fontsize=8)

        # Save the figure to path name constructed from var name
        figure_fname = os.path.join(self.figures_dir, stat_to_plot) + "_1d.png"
        fig.savefig(figure_fname, dpi=self.dpi)
        return figure_fname

    def generate_all_1D_figures(self):
        """ Loop over 1D stats variables in meta_log and generate figures. """
        # Loop over stats variables and generate figures
        figure_fnames = []
        for stats in self.meta_log.stats_vars:
            stats_fname = self.generate_1D_figure(self.meta_log.time_vars[0],
                                                  stats)
            figure_fnames.append(stats_fname)
        return figure_fnames

    def generate_all_2D_figures(self, search_variables: list,
                                target_variables: list):
        """ Generate heatmap for search experiment with 2 or more vars. """
        # Loop over stats variable combinations and generate figures
        figure_fnames = []
        for target in target_variables:
            # Only two degrees of variation - easy: don't need to fix anything
            if len(search_variables) == 2:
                stats_fname = self.generate_2D_figure(search_variables, target)
                figure_fnames.append(stats_fname)

            # Otherwise need to fix different hold-out variables to values
            elif 2 < len(search_variables) <= 4:
                all_pairs = list(itertools.combinations(search_variables, 2))
                # Loop over all 2 variable pairs to plot in heat x, y
                for pair in all_pairs:
                    to_fix = set(search_variables) - set(pair)
                    fix_values = {}
                    # Get variables to fix and their unique values
                    for k in to_fix:
                        fix_values[k] = self.hyper_log[k].unique().tolist()
                    # Create a mesh of all fix combinations of unique vals
                    all_fix_combos = list(
                                    itertools.product(*fix_values.values()))
                    for combo in all_fix_combos:
                        fixed_params = {k: combo[i] for i, k
                                        in enumerate(fix_values)}
                        stats_fname = self.generate_2D_figure(list(pair),
                                                              target,
                                                              fixed_params)
                        figure_fnames.append(stats_fname)
            # If more than 4 degrees - too many plots would be generated
            else:
                pass
        return figure_fnames

    def generate_2D_figure(self, params_to_plot, target_to_plot,
                           fixed_params=None):
        """ Generate and save 2D heatmap figure. """
        if fixed_params is not None:
            plot_subtitle = "Fixed: " + str(fixed_params)
            fname_temp = "_".join([target_to_plot] + params_to_plot)
            # Add all fixed params to figure name
            for k, v in fixed_params.items():
                fname_temp += "_" + k + "_" + str(v)
            fname_temp += "_2d.png"
        else:
            plot_subtitle = None
            fname_temp = (("_".join([target_to_plot] +
                                    params_to_plot)) + "_2d.png")
        fig, ax = visualize_2D_grid(self.hyper_log, fixed_params,
                                    params_to_plot, target_to_plot,
                                    plot_title=target_to_plot,
                                    plot_subtitle=plot_subtitle,
                                    xy_labels=params_to_plot,
                                    variable_name=target_to_plot,
                                    every_nth_tick=1, round_ticks=3,
                                    text_in_cell=False, max_heat=None)
        # Save the figure to path name constructed from var names

        figure_fname = os.path.join(self.figures_dir, fname_temp)
        fig.savefig(figure_fname, dpi=self.dpi)
        return figure_fname
