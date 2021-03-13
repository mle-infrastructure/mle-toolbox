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

import os
from dotmap import DotMap
import toml

from mle_toolbox.utils import load_mle_toolbox_config
from mle_toolbox.protocol import protocol_summary
from mle_toolbox.monitor import get_user_sge_data, get_host_sge_data


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
        Layout(name="left", ratio=0.4),
        Layout(name="center", ratio=1),
        Layout(name="right", ratio=0.5),
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
        Layout(name="f-box1"),
        Layout(name="f-box2"),
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
            "\u2022 GCS Sync Protocol: \u2714" if
            cc.general.use_gcloud_protocol_sync
            else "\u2022 GCS Sync Protocol: \u2718",
            Header.welcome_ascii[1],
            "Author: @RobertTLange",
        )
        grid.add_row(
            "\u2022 GCS Sync Results: \u2714" if
            cc.general.use_gcloud_results_storage
            else "\u2022 GCS Sync Results: \u2718",
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
    return table


def make_protocol():
    """Some example content."""
    df = protocol_summary(tail=29, verbose=False)
    table = Table(show_header=True, show_footer=False,
                    header_style="bold blue")
    table.add_column("ID", style="white", justify="left")
    table.add_column("Date")
    table.add_column("Project")
    table.add_column("Purpose")
    table.add_column("Status")
    table.add_column("Seeds")
    for index in reversed(df.index):
        row = df.iloc[index]
        table.add_row(
            row["ID"], row["Date"],  row["Project"], row["Purpose"],
            row["Status"], str(row["Seeds"])
        )
    #table.row_styles = ["none", "dim"]
    table.border_style = "blue"
    table.box = box.SIMPLE_HEAD
    return table


def make_total_experiments() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(no_wrap=True)
    message.add_row(
        "[b blue] Summary of statistics of all experiments",
    )
    return Align.center(message)


def make_last_experiment() -> Align:
    """Some example content."""
    # Add total experiments (completed, running, aborted)
    # Stored in GCS, Not yet retrieved from GCS/Local
    # Run by resource: SGE, Slurm, Local, GCP
    message = Table.grid(padding=1)
    message.add_column(no_wrap=True)
    message.add_row(
        "[b blue] Configuration of most recent experiment",
    )
    return Align.center(message)


def make_est_completion() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(no_wrap=True)
    message.add_row(
        "[b blue] Estimated completion of most recent experiment",
    )
    return Align.center(message)


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
    table.row_styles = ["none", "dim"]
    table.border_style = "white"
    table.box = box.SIMPLE_HEAD
    return table

# "[u blue link=https://github.com/sponsors/willmcgugan]https://github.com/sponsors/willmcgugan",

def make_util_plot():
    job_progress = Progress(
        "{task.description}",
        SpinnerColumn(),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    )
    job_progress.add_task("[cyan]CPU-1", total=100)
    job_progress.add_task("[cyan]CPU-2", total=100)
    job_progress.add_task("[cyan]CPU-3", total=100)
    job_progress.add_task("[cyan]CPU-4", total=100)
    job_progress.add_task("[cyan]CPU-5", total=100)
    job_progress.add_task("[cyan]CPU-6", total=100)

    total = sum(task.total for task in job_progress.tasks)
    all_progress = Progress()
    all_tasks = all_progress.add_task("MEMORY-1", total=int(total))
    all_progress.add_task("MEMORY-2", total=int(total))

    progress_table = Table.grid(expand=True)
    progress_table.add_row(
        Panel(all_progress, title="Total CPU Utilisation",
              border_style="red", padding=(3, 3)),
        Panel(job_progress, title="Total Memory Utilisation",
              border_style="red", padding=(1, 2)),
    )
    return all_progress, job_progress, all_tasks, progress_table


if __name__ == "__main__":
    layout = make_layout()
    # Fill the header with life!
    layout["header"].update(Header())
    # Fill the left-main with life!
    layout["l-box1"].update(Panel(make_user_jobs(), border_style="red",
                                title="[b red]Running Jobs by User",))
    layout["l-box2"].update(Panel(make_node_jobs(), border_style="red",
                                title="[b red]Running Jobs by Node",))
    # Fill the center-main with life!
    layout["center"].update(Panel(make_protocol(), border_style="bright_blue",
                        title="[b bright_blue]Experiment Protocol Summary",))
    # Fill the right-main with life!
    layout["r-box1"].update(Panel(make_total_experiments(), border_style="green",
                            title="[b green]Total Number of Experiment Runs",))
    layout["r-box2"].update(Panel(make_last_experiment(), border_style="green",
                            title="[b green]Last Experiment Configuration",))
    layout["r-box3"].update(Panel(make_est_completion(), border_style="green",
                    title="[b green]Estimated Time of Experiment Completion",))
    # Fill the footer with life!
    all_progress, job_progress, all_tasks, progress_table = make_util_plot()
    layout["f-box1"].update(progress_table)
    layout["f-box2"].update(Panel(make_help_commands(), border_style="white",
                    title="[b white]Help: Core MLE-Toolbox CLI Commands",))

    # Run the live updating of the dashboard
    with Live(layout, refresh_per_second=10, screen=True):
        while True:
            sleep(0.1)
            for job in job_progress.tasks:
                if not job.finished:
                    job_progress.advance(job.id)

            completed = sum(task.completed for task in job_progress.tasks)
            all_progress.update(all_tasks, completed=completed)
