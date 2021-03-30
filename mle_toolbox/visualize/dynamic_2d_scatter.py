import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from mpl_toolkits.axes_grid1 import make_axes_locatable


def animate_2D_scatter(data, dt=1,
                       ylabel="y-Axis Label", xlabel="x-Axis Label",
                       title="Animated Scatter", no_axis=False,
                       interval=100, fps=60,
                       fname="test_anim.gif", direct_save=True):
    """ Generate a gif animation of a set of 1d curves. """
    animator = AnimatedScatter(data, dt, title,
                               ylabel, xlabel, no_axis,
                               interval)
    if direct_save:
        animator.ani.save(fname, fps=fps, writer='imagemagick')
    return animator


class AnimatedScatter(object):
    """ An animated line plot of all lines in provided data over time. """
    def __init__(self, data, dt=1, title="Animated Scatter",
                 ylabel="y-Axis", xlabel="x-Axis", no_axis=False,
                 interval=100):
        self.num_steps = data.shape[0]
        # Data shape: Time, Points, (x, y)
        self.data = data
        self.t = 0
        self.dt = dt
        self.title = title

        # Setup the figure and axes...
        self.fig, self.ax = plt.subplots(figsize=(7, 7))
        self.fig.tight_layout()
        self.ax.set_ylabel(ylabel, fontsize=20)
        self.ax.set_xlabel(xlabel, fontsize=20)
        self.fig.tight_layout()

        if no_axis:
            self.ax.axis("off")

        # Plot the initial image
        x, y = data[0, :, 0], data[0, :, 1]
        self.scat = self.ax.scatter(x, y, s=5, vmin=0, vmax=1,
                                    cmap="jet", edgecolor="k")
        # orient = ax.quiver(x, y, -np.cos(theta), -np.sin(theta),
        #                    headwidth=1, headlength=3, headaxislength=3)

        # if annotate_agents:
        #     num_agents = x.shape[0]
        #     annotate = []
        #     for i in range(num_agents):
        #         temp = ax.text(x[i]+0.2, y[i]+0.2, str(i), fontsize=10)
        #         annotate.append(temp)

        # Then setup FuncAnimation.
        self.ani = animation.FuncAnimation(self.fig, self.update,
                                           frames=self.num_steps,
                                           interval=interval,
                                           init_func=self.setup_plot,
                                           blit=False)

    def setup_plot(self):
        """Initial drawing of the heatmap plot."""
        self.ax.set_title(self.title + "Time: {}".format(self.dt),
                          fontsize=40)
        self.ax.axis([-7.5, 7.5, -7.5, 7.5])
        return

    def update(self, i):
        self.t += self.dt
        self.ax.set_title(self.title + r" $t={:.1f}$".format(self.t),
                          fontsize=25)

        coord = self.data[i, :, :2]
        # theta = self.data[i, :, 2]
        self.scat.set_offsets(coord)
        # orient.set_offsets(coord)
        # orient.set_UVC(-np.cos(theta), -np.sin(theta))

        # # Update agent id annotation
        # if annotate_agents:
        #     for i in range(num_agents):
        #         annotate[i].set_position(coord[i]+0.2)

        # We need to return the updated artist for FuncAnimation to draw..
        # Note that it expects a sequence of artists, thus the trailing comma.
        return self.scat,
