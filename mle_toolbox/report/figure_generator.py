import os
from mle_toolbox.utils import load_log, hyper_log_to_df
from mle_toolbox.visualize import visualize_1D_lcurves


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
        self.meta_log = load_log(os.path.join(experiment_dir,
                                              self.meta_log_fname))
        self.hyper_log = hyper_log_to_df(os.path.join(experiment_dir,
                                                      self.hyper_log_fname))

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
        run_ids = list(self.meta_log.keys())
        time_vars = list(self.meta_log[run_ids[0]].time.keys())
        stats_vars = list(self.meta_log[run_ids[0]].stats.keys())

        # Loop over stats variables and generate figures
        figure_fnames = []
        for stats in stats_vars:
            stats_fname = self.generate_1D_figure(time_vars[0], stats)
            figure_fnames.append(stats_fname)
        return figure_fnames

    def generate_all_2D_figures(self):
        """ TODO: Also generate 2D heatmap combination figures?! """
        raise NotImplementedError
