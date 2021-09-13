import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def animate_3D_scatter(
    data,
    dt=1,
    ylabel="y-Axis Label",
    xlabel="x-Axis Label",
    zlabel="z-Axis Label",
    title="Animated Scatter",
    no_axis=False,
    interval=100,
    fps=60,
    fname="test_anim.gif",
    direct_save=True,
):
    """Generate a gif animation of a set of 1d curves."""
    animator = Animated3DScatter(
        data, dt, title, ylabel, xlabel, zlabel, no_axis, interval
    )
    if direct_save:
        animator.ani.save(fname, fps=fps, writer="imagemagick")
    return animator


class Animated3DScatter(object):
    """An animated line plot of all lines in provided data over time."""

    def __init__(
        self,
        data,
        dt=1,
        title="Animated Scatter",
        ylabel="y-Axis",
        xlabel="x-Axis",
        zlabel="z-Axis",
        no_axis=False,
        interval=100,
    ):
        self.num_steps = data.shape[0]
        # Data shape: Time, Points, (x, y)
        self.data = data
        self.t = 0
        self.dt = dt
        self.title = title

        # Setup the figure and axes...
        self.fig = plt.figure(figsize=(7, 7))
        self.ax = self.fig.add_subplot(111, projection="3d")
        self.fig.tight_layout()
        self.ax.set_ylabel(ylabel, fontsize=20, labelpad=12)
        self.ax.set_xlabel(xlabel, fontsize=20, labelpad=12)
        self.ax.set_zlabel(zlabel, fontsize=20, labelpad=12)
        self.ax.dist = 11
        self.fig.tight_layout()

        if no_axis:
            self.ax.axis("off")

        # Plot the initial image
        x, y, z = data[0, :, 0], data[0, :, 1], data[0, :, 2]

        (self.scat,) = self.ax.plot(x, y, z, linestyle="", marker="o")

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
        self.ax.set_title(self.title + "Time: {}".format(self.dt), fontsize=40, pad=-25)
        # print(x_coord, y_coord, z_coord)
        self.ax.axis(
            [
                np.min(self.data[:, :, 0]),
                np.max(self.data[:, :, 0]),
                np.min(self.data[:, :, 1]),
                np.max(self.data[:, :, 1]),
            ]
        )
        self.ax.set_zlim(np.min(self.data[:, :, 2]), np.max(self.data[:, :, 2]))
        return

    def update(self, i):
        self.t += self.dt
        self.ax.set_title(
            self.title + r" $t={:.1f}$".format(self.t), fontsize=25, pad=-25
        )
        coord = self.data[i, :, :3]
        self.scat.set_data(coord[:, 0], coord[:, 1])
        self.scat.set_3d_properties(coord[:, 2])
        # We need to return the updated artist for FuncAnimation to draw..
        # Note that it expects a sequence of artists, thus the trailing comma.
        return (self.scat,)
