import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import seaborn as sns


def animate_1D_lines(data, dt=1, line_labels=None, base_label="",
                     ylabel="y-Axis Label", xlabel="x-Axis Label",
                     title="Animated Lines", interval=100, fps=60,
                     fname="test_anim.gif", direct_save=True):
    """ Generate a gif animation of a set of 1d curves. """
    animator = AnimatedLine(data, dt, title, line_labels, base_label,
                            ylabel, xlabel, interval)
    if direct_save:
        animator.ani.save(fname, fps=fps, writer='imagemagick')
    return animator


class AnimatedLine(object):
    """ An animated line plot of all lines in provided data over time. """
    def __init__(self, data, dt=1, title="Animated Lines", line_labels=None,
                 base_label="", ylabel="y-Axis", xlabel="Time", interval=100):
        self.num_steps = data.shape[0]
        self.num_lines = data.shape[1]
        sns.set_palette(sns.color_palette("coolwarm", self.num_lines))

        self.data = data #np.vstack([data, np.zeros((10, data.shape[1]))])
        self.t = 0
        self.dt = dt
        self.title = title
        self.line_labels = line_labels
        self.base_label = base_label

        # Setup the figure and axes...
        self.fig, self.ax = plt.subplots(figsize=(7, 5))
        self.fig.tight_layout()
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)
        self.ax.set_ylabel(ylabel, fontsize=20)
        self.ax.set_xlabel(xlabel, fontsize=20)

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
        """Initial drawing of the scatter plot."""
        y = self.data[:1, :]
        self.line = []
        for l_id in range(self.num_lines):
            if self.line_labels is not None:
                label = self.base_label + " " + str(self.line_labels[l_id])
            else:
                label = self.base_label + " " + str(l_id + 1)
            self.line.append(self.ax.plot(np.arange(0, self.dt*y.shape[0],
                                                    self.dt),
                                          y[0, l_id], label=label)[0])

        self.ax.legend(fontsize=15, loc=2)
        self.ax.axis([0, self.dt*self.num_steps,
                      np.min(self.data)-0.5,
                      np.max(self.data)+0.5])
        self.ax.set_title(self.title + r": $t={}$".format(self.t+1),
                          fontsize=15)
        # For FuncAnimation's sake, we need to return the artist we'll be using
        # Note that it expects a sequence of artists, thus the trailing comma.
        return self.line,

    def update(self, i):
        sub_data = self.data[:(i+1), :]
        for l_id, l in enumerate(self.line):
            l.set_data(np.arange(0, self.dt*sub_data.shape[0], self.dt),
                       sub_data[:, l_id])
        self.t = self.t + self.dt
        self.ax.set_title(self.title + r" $t={:.1f}$".format(self.t),
                          fontsize=25)
        self.fig.tight_layout()
        # We need to return the updated artist for FuncAnimation to draw..
        # Note that it expects a sequence of artists, thus the trailing comma.
        return self.line,
