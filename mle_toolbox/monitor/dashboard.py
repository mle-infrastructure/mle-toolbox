from datetime import datetime
from time import sleep
from rich import box
from rich.align import Align
from rich.console import Console, RenderGroup
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

import os
from dotmap import DotMap
import numpy as np
import toml
import termplotlib as tpl

from mle_toolbox.utils import load_mle_toolbox_config
from mle_toolbox.protocol import protocol_summary, load_local_protocol_db
from mle_toolbox.monitor import get_user_sge_data, get_host_sge_data


"""
TODOS:
- Work with local_db data and fill right columns
    - Total experiment stats
    - Last experiment config summary
    - Estimated time of completion [Need cancelation/Estimate in db]
- Make qstat calls a lot more efficient
- Get all CPU slots occupied, memory used, GPU usage? -> ask Dom
- Figure out how to store data in time series plots -> Moving average
- Make sure that reloading works by starting a new experiment
- Add support for slurm!
- Add documentation/function descriptions
"""


def load_mle_toolbox_config():
    """ Load cluster config from the .toml file. See docs for more info. """
    return DotMap(toml.load(os.path.expanduser("~/mle_config.toml")),
                  _dynamic=False)

resource = "sge"
cc = load_mle_toolbox_config()

console = Console()

def make_layout() -> Layout:
    """Define the layout."""
    layout = Layout(name="root")
    # Split in three vertical sections: Welcome, core info, help + util plots
    layout.split(
        Layout(name="header", size=7),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=10),
    )
    # Split center into 3 horizontal sections
    layout["main"].split(
        Layout(name="left", ratio=0.375),
        Layout(name="center", ratio=1),
        Layout(name="right", ratio=0.4),
        direction="horizontal",
    )
    # Split center left into user info and node info
    layout["left"].split(Layout(name="l-box1", size=10),
                         Layout(name="l-box2", size=25))
    # Split center right into total experiments, last experiments, ETA
    layout["right"].split(Layout(name="r-box1", size=12),
                          Layout(name="r-box2", size=12),
                          Layout(name="r-box3", size=11))
    # Split bottom into toolbox command info and cluster util termplots
    layout["footer"].split(
        Layout(name="f-box1", ratio=0.5),
        Layout(name="f-box2", ratio=0.5),
        Layout(name="f-box3", ratio=1),
        direction="horizontal"
    )
    return layout


class Header:
    """Display header with clock."""
    welcome_ascii = """            __  _____    ______   ______            ____
           /  |/  / /   / ____/  /_  __/___  ____  / / /_  ____  _  __
          / /|_/ / /   / __/______/ / / __ \/ __ \/ / __ \/ __ \| |/_/
         / /  / / /___/ /__/_____/ / / /_/ / /_/ / / /_/ / /_/ />  <
        /_/  /_/_____/_____/    /_/  \____/\____/_/_.___/\____/_/|_|
    """.splitlines()
    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        grid.add_row(
            "General Settings:", Header.welcome_ascii[0],
            datetime.now().ctime().replace(":", "[blink]:[/]"),
        )
        grid.add_row(
            "\u2022 GCS Sync Protocol: [green]:heavy_check_mark:" if
            cc.general.use_gcloud_protocol_sync
            else "\u2022 GCS Sync Protocol: [red]:x:",
            Header.welcome_ascii[1],
            "Author: @RobertTLange",
        )
        grid.add_row(
            "\u2022 GCS Sync Results: [green]:heavy_check_mark:" if
            cc.general.use_gcloud_results_storage
            else "\u2022 GCS Sync Results: [red]:x:",
            Header.welcome_ascii[2],
            f"Resource: {resource}",
        )
        grid.add_row(
            f"\u2022 DB Path: {cc.general.local_protocol_fname}",
            Header.welcome_ascii[3],
            f"User: {cc[resource].credentials.user_name}",
        )
        grid.add_row(
            f"\u2022 Env Name: {cc.general.remote_env_name}",
            Header.welcome_ascii[4],
            "Hi there! [not italic]:hugging_face:[/]",
        )
        return Panel(grid, style="white on blue")


def make_user_jobs() -> Align:
    """Some example content."""
    user_data = get_user_sge_data()
    sum_all = str(sum([r[1] for r in user_data]))
    sum_running = str(sum([r[2] for r in user_data]))
    sum_login = str(sum([r[3] for r in user_data]))

    table = Table(show_header=True, show_footer=False,
                  header_style="bold red")
    table.add_column("USER", Text.from_markup("[b]Total", justify="right"),
                     style="white", justify="left")
    table.add_column("ALL", sum_all)
    table.add_column("RUN", sum_running)
    table.add_column("LOGIN", sum_login)
    for row in user_data:
        table.add_row(row[0], str(row[1]), str(row[2]), str(row[3]))
    table.show_footer = True
    table.row_styles = ["none", "dim"]
    table.border_style = "red"
    table.box = box.SIMPLE
    return table


def make_node_jobs() -> Align:
    """Some example content."""
    host_data = get_host_sge_data()
    sum_all = str(sum([r[1] for r in host_data]))
    sum_running = str(sum([r[2] for r in host_data]))
    sum_login = str(sum([r[3] for r in host_data]))

    table = Table(show_header=True, show_footer=False,
                  header_style="bold red")
    table.add_column("NODE", Text.from_markup("[b]Total", justify="right"),
                     style="white", justify="left")
    table.add_column("ALL", sum_all)
    table.add_column("RUN", sum_running)
    table.add_column("LOGIN", sum_login)
    for row in host_data:
        table.add_row(row[0], str(row[1]), str(row[2]), str(row[3]))
    table.show_footer = True
    table.row_styles = ["none", "dim"]
    table.border_style = "red"
    table.box = box.SIMPLE
    return Align.center(table)


def make_protocol() -> Table:
    """Some example content."""
    df = protocol_summary(tail=29, verbose=False)
    table = Table(show_header=True, show_footer=False,
                  header_style="bold blue")
    table.add_column("ID", justify="left")
    table.add_column("Date")
    table.add_column("Project")
    table.add_column("Purpose")
    table.add_column("-")
    table.add_column("Seeds", justify="center")
    table.add_column("Resource")
    for index in reversed(df.index):
        row = df.iloc[index]
        if row["Status"] == "running":
            status = Spinner('dots', style="magenta")
        elif row["Status"] == "completed":
            status = "[green]:heavy_check_mark:"
        else:
            status = "[red]:x:"
        table.add_row(
            row["ID"], row["Date"],  row["Project"], row["Purpose"],
            status, str(row["Seeds"]), str(row["Resource"][:12]))
    # table.caption = "Experiment Status - \
    #                 [green]:heavy_check_mark::[/green] Completed, \
    #                 [red]:x::[/red] Aborted, [magenta].[/magenta] Running"
    table.border_style = "blue"
    table.box = box.SIMPLE_HEAD
    return Align.center(table)


def make_total_experiments() -> Align:
    """Some example content."""
    # Add total experiments (completed, running, aborted)
    # Stored in GCS, Not yet retrieved from GCS/Local
    # Run by resource: SGE, Slurm, Local, GCP
    # Reports generated
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    table = Table(show_header=True, show_footer=False,
                  header_style="bold yellow")
    table.add_column("Total")
    table.add_column("Run")
    table.add_column("Done")
    table.add_column("Aborted")
    table.add_row(str(last_experiment_id), "1", "1", "1")
    table.add_row(Text.from_markup("[b yellow]SGE"),
                  Text.from_markup("[b yellow]Slurm"),
                  Text.from_markup("[b yellow]GCP"),
                  Text.from_markup("[b yellow]Local"),)
    table.add_row("1", "1", "1", "1")
    table.add_row(Text.from_markup("[b yellow]-"),
                  Text.from_markup("[b yellow]Report"),
                  Text.from_markup("[b yellow]GCS"),
                  Text.from_markup("[b yellow]Retrieved"),)
    table.add_row("-", "1", "1", "1")
    #table.row_styles = ["none", "dim"]
    table.border_style = "yellow"
    table.box = box.SIMPLE_HEAD
    return Align.center(table)


def make_last_experiment() -> Align:
    """Some example content."""
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    table = Table(show_header=True, show_footer=False,
                  header_style="bold yellow")
    table.add_column("Total")
    table.add_column("Run")
    table.add_column("Done")
    table.add_column("Aborted")
    table.add_row(str(last_experiment_id), "1", "1", "1")
    table.add_row(Text.from_markup("[b yellow]SGE"),
                  Text.from_markup("[b yellow]Slurm"),
                  Text.from_markup("[b yellow]GCP"),
                  Text.from_markup("[b yellow]Local"),)
    table.add_row("1", "1", "1", "1")
    table.add_row(Text.from_markup("[b yellow]-"),
                  Text.from_markup("[b yellow]Report"),
                  Text.from_markup("[b yellow]GCS"),
                  Text.from_markup("[b yellow]Retrieved"),)
    table.add_row("-", "1", "1", "1")
    #table.row_styles = ["none", "dim"]
    table.border_style = "yellow"
    table.box = box.SIMPLE_HEAD
    return Align.center(table)


def make_est_completion() -> Align:
    """Some example content."""
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    table = Table(show_header=True, show_footer=False,
                  header_style="bold yellow")
    table.add_column("Total")
    table.add_column("Run")
    table.add_column("Done")
    table.add_column("Aborted")
    table.add_row(str(last_experiment_id), "1", "1", "1")
    table.add_row(Text.from_markup("[b yellow]SGE"),
                  Text.from_markup("[b yellow]Slurm"),
                  Text.from_markup("[b yellow]GCP"),
                  Text.from_markup("[b yellow]Local"),)
    table.add_row("1", "1", "1", "1")
    table.add_row(Text.from_markup("[b yellow]-"),
                  Text.from_markup("[b yellow]Report"),
                  Text.from_markup("[b yellow]GCS"),
                  Text.from_markup("[b yellow]Retrieved"),)
    table.add_row("-", "1", "1", "1")
    #table.row_styles = ["none", "dim"]
    table.border_style = "yellow"
    table.box = box.SIMPLE_HEAD
    return Align.center(table)


def make_help_commands() -> Align:
    """Some example content."""
    table = Table(show_header=True, show_footer=False,
                    header_style="bold magenta")
    table.add_column("Command", style="white", justify="left")
    table.add_column("Options", )
    table.add_column("Function", )
    table.add_row(
        "run-experiment",
        "[b blue]--no_protocol, --no_welcome, --resource_to_run, --purpose",
        "[b red] Start up from .yaml config",
    )
    table.add_row(
        "retrieve-experiment",
        "[b blue]-e_id, -fig_dir, -exp_dir",
        "[b red] Retrieve from remote GCS",
    )
    table.add_row(
        "report-experiment",
        "[b blue]--experiment_id",
        "[b red] Generate .md, .html report",
    )
    table.add_row(
        "monitor-cluster",
        "[b blue]None",
        "[b red] Monitor resource usage",
    )
    #table.row_styles = ["none", "dim"]
    table.border_style = "white"
    table.box = box.SIMPLE_HEAD
    return table

# "[u blue link=https://github.com/sponsors/willmcgugan]https://github.com/sponsors/willmcgugan",

def make_cpu_util_plot() -> Align:
    x = np.linspace(0, 2 * np.pi, 10)
    y = np.sin(x)
    fig = tpl.figure()
    fig.plot(x, y, xlabel="Time", width=40, height=10)
    plot_str = fig.get_string()
    message = Table.grid()
    message.add_column(no_wrap=True)
    message.add_row(plot_str,)
    return Align.center(message)


def make_memory_util_plot() -> Align:
    x = np.linspace(0, 2 * np.pi, 10)
    y = np.cos(x)

    fig = tpl.figure()
    fig.plot(x, y, xlabel="Time", width=40, height=10)
    plot_str = fig.get_string()
    message = Table.grid()
    message.add_column(no_wrap=True)
    message.add_row(plot_str,)
    return Align.center(message)


if __name__ == "__main__":
    if cc.general.use_gcloud_protocol_sync:
        try:
            # Import of helpers for GCloud storage of results/protocol
            from mle_toolbox.remote.gcloud_transfer import get_gcloud_db
            accessed_remote_db = get_gcloud_db()
        except ImportError as err:
            raise ImportError("You need to install `google-cloud-storage` to "
                              "synchronize protocols with GCloud. Or set "
                              "`use_glcoud_protocol_sync = False` in your "
                              "config file.")

    layout = make_layout()
    # Fill the header with life!
    layout["header"].update(Header())
    # Fill the left-main with life!
    layout["l-box1"].update(Panel(make_user_jobs(), border_style="red",
                                title="Scheduled Jobs by User",))
    layout["l-box2"].update(Panel(make_node_jobs(), border_style="red",
                                title="Running Jobs by Node",))
    # Fill the center-main with life!
    layout["center"].update(Panel(make_protocol(), border_style="bright_blue",
                        title="Experiment Protocol Summary",))
    # Fill the right-main with life!
    layout["r-box1"].update(Panel(make_total_experiments(), border_style="yellow",
                            title="Total Number of Experiment Runs",))
    layout["r-box2"].update(Panel(make_last_experiment(), border_style="yellow",
                            title="Last Experiment Configuration",))
    layout["r-box3"].update(Panel(make_est_completion(), border_style="yellow",
                    title="Est. Experiment Completion Time",))
    # Fill the footer with life!
    layout["f-box1"].update(Panel(make_cpu_util_plot(),
                                  title="Total CPU Utilisation",
                                  border_style="red"),)
    layout["f-box2"].update(Panel(make_memory_util_plot(),
                                  title="Total Memory Utilisation",
                                  border_style="red"))
    layout["f-box3"].update(Panel(make_help_commands(), border_style="white",
                    title="[b white]Help: Core MLE-Toolbox CLI Commands",))

    # Run the live updating of the dashboard
    with Live(layout, refresh_per_second=10, screen=True):
        while True:
            # Every 10 minutes pull the newest DB from GCS
            sleep(600)
            if cc.general.use_gcloud_protocol_sync:
                accessed_remote_db = get_gcloud_db()
