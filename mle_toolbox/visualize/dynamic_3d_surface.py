import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def animate_3D_surface(
    x,
    y,
    data,
    dt=1,
    ylabel="y-Axis Label",
    xlabel="x-Axis Label",
    zlabel="z-Axis Label",
    title="Animated Surface",
    no_axis=False,
    interval=100,
    fps=60,
    cmap="magma",
    fname="test_anim.gif",
    direct_save=True,
):
    """Generate a gif animation of a set of 1d curves."""
    animator = Animated3DSurface(
        x, y, data, dt, title, ylabel, xlabel, zlabel, no_axis, interval, cmap
    )
    if direct_save:
        animator.ani.save(fname, fps=fps, writer="imagemagick")
    return animator


class Animated3DSurface(object):
    """An animated line plot of all lines in provided data over time."""

    def __init__(
        self,
        x,
        y,
        data,
        dt=1,
        title="Animated Scatter",
        ylabel="y-Axis",
        xlabel="x-Axis",
        zlabel="z-Axis",
        no_axis=False,
        interval=100,
        cmap="magma",
    ):
        self.num_steps = data.shape[0]
        # Data shape: Time, Points, (x, y)
        self.x = x
        self.y = y
        self.data = data
        self.t = 0
        self.dt = dt
        self.title = title
        self.cmap = cmap

        # Setup the figure and axes...
        self.fig = plt.figure(figsize=(7, 7))
        self.ax = self.fig.add_subplot(111, projection="3d")
        # self.fig.tight_layout()
        self.ax.set_ylabel(ylabel, fontsize=20, labelpad=12)
        self.ax.set_xlabel(xlabel, fontsize=20, labelpad=12)
        self.ax.set_zlabel(zlabel, fontsize=20, labelpad=12)
        # self.ax.dist = 12
        # self.fig.tight_layout()

        if no_axis:
            self.ax.axis("off")

        # make the panes transparent
        self.ax.xaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        self.ax.yaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        self.ax.zaxis.set_pane_color((1.0, 1.0, 1.0, 0.0))
        # make the grid lines transparent
        self.ax.xaxis._axinfo["grid"]["color"] = (1, 1, 1, 0)
        self.ax.yaxis._axinfo["grid"]["color"] = (1, 1, 1, 0)
        self.ax.zaxis._axinfo["grid"]["color"] = (1, 1, 1, 0)

        # Plot the initial image
        self.surface = [
            self.ax.plot_surface(
                self.x, self.y, self.data[0, :, :], color="0.75", rstride=1, cstride=1
            )
        ]

        # Then setup FuncAnimation.
        self.ani = animation.FuncAnimation(
            self.fig,
            self.update,
            frames=self.num_steps,
            interval=interval,
            init_func=self.setup_plot,
            blit=False,
        )

    def setup_plot(self):
        """Initial drawing of the heatmap plot."""
        timestr = self.title + r" $t={:.1f}$".format(self.t)
        self.ax.set_title(timestr.ljust(30), fontsize=25, pad=-55)
        # print(x_coord, y_coord, z_coord)
        self.ax.set_zlim(np.min(self.data), np.max(self.data))
        return

    def update(self, i):
        self.t += self.dt
        timestr = self.title + r" $t={:.1f}$".format(self.t)
        self.ax.set_title(timestr.ljust(30), fontsize=25, pad=-55)
        self.surface[0].remove()
        self.surface[0] = self.ax.plot_surface(
            self.x, self.y, self.data[i, :, :], cmap=self.cmap
        )
        # We need to return the updated artist for FuncAnimation to draw..
        # Note that it expects a sequence of artists, thus the trailing comma.
        return (self.surface,)
