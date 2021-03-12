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
        Layout(name="left"),
        Layout(name="center"),
        Layout(name="right"),
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
    welcome_ascii = """__  _____    ______   ______            ____
             /  |/  / /   / ____/  /_  __/___  ____  / / /_  ____  _  __
            / /|_/ / /   / __/______/ / / __ \/ __ \/ / __ \/ __ \| |/_/
         / /  / / /___/ /__/_____/ / / /_/ / /_/ / / /_/ / /_/ />  <
        /_/  /_/_____/_____/    /_/  \____/\____/_/_.___/\____/_/|_|
    """.splitlines()
    def __rich__(self) -> Panel:
        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="center")
        grid.add_column(justify="right")
        # grid.add_row(
        #     "[b]Rich[/b] Layout application",
        #     datetime.now().ctime().replace(":", "[blink]:[/]"),
        #     "[b]Rich[/b] Layout application",
        # )
        # grid.add_row(
        #     datetime.now().ctime().replace(":", "[blink]:[/]"),
        #     "[b]Rich[/b] Layout application",
        #     "[b]Rich[/b] Layout application",
        # )
        for r in Header.welcome_ascii:
            grid.add_row("", r, "")
        return Panel(grid, style="white on blue")


def make_node_jobs() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(style="green", justify="right")
    message.add_column(no_wrap=True)
    message.add_row(
        "Fill with",
        "[b blue] Active Jobs on Different Cluster Nodes",
    )
    return Align.center(message)


def make_user_jobs() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(style="green", justify="right")
    message.add_column(no_wrap=True)
    message.add_row(
        "Fill with",
        "[b blue] Active Jobs for Different Cluster Users",
    )
    return Align.center(message)

def make_protocol() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(style="green", justify="right")
    message.add_column(no_wrap=True)
    message.add_row(
        "Fill with",
        "[b blue] Protocol Summary of recent experiments",
    )
    return Align.center(message)


def make_total_experiments() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(style="green", justify="right")
    message.add_column(no_wrap=True)
    message.add_row(
        "Fill with",
        "[b blue] Summary of statistics of all experiments",
    )
    return Align.center(message)


def make_last_experiment() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(style="green", justify="right")
    message.add_column(no_wrap=True)
    message.add_row(
        "Fill with",
        "[b blue] Configuration of most recent experiment",
    )
    return Align.center(message)


def make_est_completion() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(style="green", justify="right")
    message.add_column(no_wrap=True)
    message.add_row(
        "Fill with",
        "[b blue] Estimated completion of most recent experiment",
    )
    return Align.center(message)


def make_help_commands() -> Align:
    """Some example content."""
    message = Table.grid(padding=1)
    message.add_column(style="green", justify="right")
    message.add_column(no_wrap=True)
    message.add_row(
        "Fill with",
        "[b blue] Overview of MLE-Toolbox commands",
    )
    return Align.center(message)

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
                    title="[b white]Help: Core MLE-Toolbox Commands",))

    # Run the live updating of the dashboard
    with Live(layout, refresh_per_second=10, screen=True):
        while True:
            sleep(0.1)
            for job in job_progress.tasks:
                if not job.finished:
                    job_progress.advance(job.id)

            completed = sum(task.completed for task in job_progress.tasks)
            all_progress.update(all_tasks, completed=completed)
