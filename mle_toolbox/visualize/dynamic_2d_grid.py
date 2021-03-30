import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1 import make_axes_locatable


def animate_2D_grid(data, var_name="A Variable", dt=1,
                    ylabel="y-Axis Label", xlabel="x-Axis Label",
                    range_y=None, range_x=None, every_nth=1, round_ticks=1,
                    vmin=None, vmax=None,
                    title="Animated Grid", interval=100, fps=60,
                    fname="test_anim.gif", direct_save=True):
    """ Generate a gif animation of a set of 1d curves. """
    animator = AnimatedGrid(data, var_name, dt, title,
                            ylabel, xlabel, range_y, range_x,
                            every_nth, round_ticks, vmin, vmax,
                            interval)
    if direct_save:
        animator.ani.save(fname, fps=fps, writer='imagemagick')
    return animator


class AnimatedGrid(object):
    """ An animated line plot of all lines in provided data over time. """
    def __init__(self, data, var_name="A Variable", dt=1,
                 title="Animated Grid",
                 ylabel="y-Axis", xlabel="Time",
                 range_y=None, range_x=None, every_nth=1, round_ticks=1,
                 vmin=None, vmax=None, interval=100):
        self.num_steps = data.shape[0]
        self.data = data
        self.t = 0
        self.dt = dt
        self.title = title
        self.range_x = (range_x if range_x is not None
                        else np.arange(data.shape[1]))
        self.range_y = (range_y if range_y is not None
                        else np.arange(data.shape[2]))
        self.var_name = var_name
        self.every_nth = every_nth
        self.round_ticks = round_ticks

        # Setup the figure and axes...
        self.fig, self.ax = plt.subplots(figsize=(7, 7))
        self.fig.tight_layout()
        self.ax.set_ylabel(ylabel, fontsize=20)
        self.ax.set_xlabel(xlabel, fontsize=20)

        # Plot the initial image
        self.im = self.ax.imshow(np.zeros(self.data[0].shape),
                                 cmap="Reds", vmin=vmin, vmax=vmax)

        for tick in self.ax.xaxis.get_major_ticks():
            tick.label.set_fontsize(20)
        for tick in self.ax.yaxis.get_major_ticks():
            tick.label.set_fontsize(20)
        # Then setup FuncAnimation.
        self.ani = animation.FuncAnimation(self.fig, self.update,
                                           frames=self.num_steps,
                                           interval=interval,
                                           init_func=self.setup_plot,
                                           blit=False)
        self.fig.tight_layout()

    def setup_plot(self):
        """Initial drawing of the heatmap plot."""
        self.im.set_data(np.zeros(self.data[0].shape))
        self.ax.set_title(self.title + " {}".format(1))
        # We want to show all ticks...
        self.ax.set_yticks(np.arange(len(self.range_y)))

        if len(self.range_y) != 0:
            if type(self.range_y[-1]) is not str:
                if self.round_ticks != 0:
                    yticklabels = [str(round(float(label), self.round_ticks))
                                   for label in self.range_y[::-1]]
                else:
                    yticklabels = [str(int(label))
                                   for label in self.range_y[::-1]]
            else:
                yticklabels = [str(label) for label in self.range_y[::-1]]
        else:
            yticklabels = []
        self.ax.set_yticklabels(yticklabels)

        for n, label in enumerate(self.ax.yaxis.get_ticklabels()):
            if n % self.every_nth != 0:
                label.set_visible(False)

        self.ax.set_xticks(np.arange(len(self.range_x)))
        if len(self.range_x) != 0:
            if type(self.range_x[-1]) is not str:
                if self.round_ticks != 0:
                    xticklabels = [str(round(float(label), self.round_ticks))
                                   for label in self.range_x]
                else:
                    xticklabels = [str(int(label))
                                   for label in self.range_x]
            else:
                xticklabels = [str(label) for label in self.range_x]
        else:
            xticklabels = []
        self.ax.set_xticklabels(xticklabels)

        for n, label in enumerate(self.ax.xaxis.get_ticklabels()):
            if n % self.every_nth != 0:
                label.set_visible(False)

        # Rotate the tick labels and set their alignment.
        plt.setp(self.ax.get_xticklabels(), rotation=45, ha="right",
                 rotation_mode="anchor")

        divider = make_axes_locatable(self.ax)
        cax = divider.append_axes("right", size="7%", pad=0.15)
        cbar = self.fig.colorbar(self.im, cax=cax)
        cbar.set_label(self.var_name, rotation=270, labelpad=30)
        self.fig.tight_layout()
        return

    def update(self, i):
        sub_data = self.data[i]
        self.t += self.dt
        self.im.set_data(sub_data)
        self.ax.set_title(self.title + r" $t={:.1f}$".format(self.t),
                          fontsize=25)
        # We need to return the updated artist for FuncAnimation to draw..
        # Note that it expects a sequence of artists, thus the trailing comma.
        return self.im,
