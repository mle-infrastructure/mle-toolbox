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

import time
import datetime as dt
import numpy as np
import termplotlib as tpl

from mle_toolbox.utils import (load_mle_toolbox_config,
                               determine_resource)
from mle_toolbox.protocol import (protocol_summary,
                                  load_local_protocol_db)
from mle_toolbox.monitor.monitor_sge import (get_user_sge_data,
                                             get_host_sge_data,
                                             get_utilisation_sge_data)
from mle_toolbox.monitor.monitor_db import (get_total_experiments,
                                            get_time_experiment,
                                            get_last_experiment)

"""
TODOS:
- Make qstat calls a lot more efficient -> Faster at startup
- Add support for slurm, local + gcp!
- Add documentation/function descriptions
- Link Author @RobertTLange to twitter account
"""

cc = load_mle_toolbox_config()
console = Console()

def make_layout() -> Layout:
    """ Define the dashboard layout."""
    layout = Layout(name="root")
    # Split in three vertical sections: Welcome, core info, help + util plots
    layout.split(
        Layout(name="header", size=7),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=10),
    )
    # Split center into 3 horizontal sections
    layout["main"].split(
        Layout(name="left", ratio=0.3),
        Layout(name="center", ratio=1),
        Layout(name="right", ratio=0.35),
        direction="horizontal",
    )
    # Split center left into user info and node info
    layout["left"].split(Layout(name="l-box1", size=10),
                         Layout(name="l-box2", size=25))
    # Split center right into total experiments, last experiments, ETA
    layout["right"].split(Layout(name="r-box1", ratio=0.3),
                          Layout(name="r-box2", ratio=0.4),
                          Layout(name="r-box3", ratio=0.35))
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
            dt.datetime.now().ctime().replace(":", "[blink]:[/]"),
        )
        grid.add_row(
            "\u2022 GCS Sync Protocol: [green]:heavy_check_mark:" if
            cc.general.use_gcloud_protocol_sync
            else "\u2022 GCS Sync Protocol: [red]:heavy_multiplication_x:",
            Header.welcome_ascii[1],
            "Author: @RobertTLange :bird:",
            # TODO: Figure out why link won't work if we use text != url
            #[u white link=https://twitter.com/RobertTLange]
        )
        resource = determine_resource()
        if resource == "sge-cluster":
            res = "sge"
        elif resource == "slurm-cluster":
            res = "slurm"

        grid.add_row(
            "\u2022 GCS Sync Results: [green]:heavy_check_mark:" if
            cc.general.use_gcloud_results_storage
            else "\u2022 GCS Sync Results: [red]:heavy_multiplication_x:",
            Header.welcome_ascii[2],
            f"Resource: {resource}",
        )
        grid.add_row(
            f"\u2022 DB Path: {cc.general.local_protocol_fname}",
            Header.welcome_ascii[3],
            f"User: {cc[res].credentials.user_name}",
        )
        grid.add_row(
            f"\u2022 Env Name: {cc.general.remote_env_name}",
            Header.welcome_ascii[4],
            "Hi there! [not italic]:hugging_face:[/]",
        )
        return Panel(grid, style="white on blue")


def make_user_jobs(user_data) -> Align:
    """Some example content."""
    sum_all = str(sum([r[1] for r in user_data]))
    sum_running = str(sum([r[2] for r in user_data]))
    sum_login = str(sum([r[3] for r in user_data]))

    table = Table(show_header=True, show_footer=False,
                  header_style="bold red")
    table.add_column("USER", Text.from_markup("[b]Total", justify="right"),
                     style="white", justify="left")
    table.add_column("ALL", sum_all, justify="center")
    table.add_column("RUN", sum_running, justify="center")
    table.add_column("LOGIN", sum_login, justify="center")
    for row in user_data:
        table.add_row(row[0], str(row[1]), str(row[2]), str(row[3]))
    table.show_footer = True
    table.row_styles = ["none", "dim"]
    table.border_style = "red"
    table.box = box.SIMPLE
    return Align.center(table)


def make_node_jobs(host_data) -> Align:
    """Some example content."""
    sum_all = str(sum([r[1] for r in host_data]))
    sum_running = str(sum([r[2] for r in host_data]))
    sum_login = str(sum([r[3] for r in host_data]))

    table = Table(show_header=True, show_footer=False,
                  header_style="bold red")
    table.add_column("NODE", Text.from_markup("[b]Total", justify="right"),
                     style="white", justify="left")
    table.add_column("ALL", sum_all, justify="center")
    table.add_column("RUN", sum_running, justify="center")
    table.add_column("LOGIN", sum_login, justify="center")
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
    sta_str = "[green]:heavy_check_mark:[/green]/[red]:heavy_multiplication_x:"
    table.add_column(sta_str, justify="center")
    table.add_column("E-ID")
    table.add_column("Date")
    table.add_column("Project")
    table.add_column("Purpose")
    table.add_column("Type")
    table.add_column("[yellow]:arrow_forward:", justify="center")
    table.add_column("#Jobs", justify="center")
    table.add_column("#CPU", justify="center")
    table.add_column("#GPU", justify="center")
    table.add_column("[yellow]:recycle:", justify="center")
    for index in reversed(df.index):
        row = df.iloc[index]
        if row["Resource"] == "sge-cluster":
            resource = "SGE"
        elif row["Resource"] == "sge-cluster":
            resource = "Slurm"
        elif row["Resource"] == "gcp-cloud":
            resource = "GCP"
        else:
            resource = "Local"

        if row["Status"] == "running":
            status = Spinner('dots', style="magenta")
        elif row["Status"] == "completed":
            status = "[green]:heavy_check_mark:"
        else:
            status = "[red]:heavy_multiplication_x:"
        table.add_row(status, row["ID"], row["Date"], row["Project"][:20],
                      row["Purpose"][:25], row["Type"],
                      resource, str(row["Jobs"]), str(row["CPUs"]),
                      str(row["GPUs"]), str(row["Seeds"]))
    # TODO: Figure out why entire caption is made white/colored
    # table.caption = "Experiment Status - \
    #                 [green]:heavy_check_mark::[/green] Completed, \
    #                 [red]:x::[/red] Aborted, [magenta].[/magenta] Running"
    table.border_style = "blue"
    table.box = box.SIMPLE_HEAD
    return Align.center(table)


def make_total_experiments(total_data) -> Align:
    """Some example content."""
    table = Table(show_header=False, show_footer=False,
                  header_style="bold yellow")
    table.add_column()
    table.add_column()
    table.add_column()
    table.add_column()
    table.add_row("[b yellow]Total", Spinner('dots', style="magenta"),
                  "[green]:heavy_check_mark:", "[red]:heavy_multiplication_x:")
    table.add_row(total_data["total"], total_data["run"],
                  total_data["done"], total_data["aborted"])
    table.add_row(Text.from_markup("[b yellow]SGE"),
                  Text.from_markup("[b yellow]Slurm"),
                  Text.from_markup("[b yellow]GCP"),
                  Text.from_markup("[b yellow]Local"),)
    table.add_row(total_data["sge"], total_data["slurm"],
                  total_data["gcp"], total_data["local"])
    table.add_row(Text.from_markup("[b yellow]-"),
                  Text.from_markup("[b yellow]Report"),
                  Text.from_markup("[b yellow]GCS"),
                  Text.from_markup("[b yellow]Sync"),)
    table.add_row("-", total_data["report_gen"],
                  total_data["gcs_stored"], total_data["retrieved"])
    #table.row_styles = ["none", "dim"]
    table.border_style = "yellow"
    table.box = box.SIMPLE_HEAD
    return Align.center(table)


def make_last_experiment(last_data) -> Align:
    """Some example content."""
    table = Table(show_header=False, show_footer=False,
                  header_style="bold yellow")
    table.add_column()
    table.add_column()
    table.add_row(Text.from_markup("[b yellow]E-ID"),
                  last_data["e_id"],)
    table.add_row(Text.from_markup("[b yellow]Type"),
                  last_data["e_type"],)
    table.add_row(Text.from_markup("[b yellow]Dir."),
                  last_data["e_dir"],)
    table.add_row(Text.from_markup("[b yellow]Script"),
                  last_data["e_script"],)
    table.add_row(Text.from_markup("[b yellow]Config"),
                  last_data["e_config"],)
    # table.add_row(Text.from_markup("[b yellow]Report"),
    #               str(last_data["report_gen"]),)

    if last_data["e_type"] == "hyperparameter-search":
        table.add_row(Text.from_markup("[b yellow]Search"),
                      last_data["search_type"],)
        table.add_row(Text.from_markup("[b yellow]Metrics"),
                      str(last_data["eval_metrics"]),)

        p_counter = 0
        for k in last_data["params_to_search"].keys():
            for var in last_data["params_to_search"][k].keys():
                if k == "categorical":
                    row = [var] + last_data["params_to_search"][k][var]
                elif k == "real":
                    try:
                        row = [var,
                               last_data["params_to_search"][k][var]["begin"],
                               last_data["params_to_search"][k][var]["end"],
                               last_data["params_to_search"][k][var]["bins"]]
                    except:
                        row = [var,
                               last_data["params_to_search"][k][var]["begin"],
                               last_data["params_to_search"][k][var]["end"],
                               last_data["params_to_search"][k][var]["prior"]]
                elif k == "integer":
                    row = [var,
                           last_data["params_to_search"][k][var]["begin"],
                           last_data["params_to_search"][k][var]["end"],
                           last_data["params_to_search"][k][var]["spacing"]]
                if p_counter == 0:
                    table.add_row(Text.from_markup("[b yellow]Params"),
                                  str(row),)
                else:
                    table.add_row("", str(row),)
                p_counter += 1

    #table.row_styles = ["none", "dim"]
    table.border_style = "yellow"
    table.box = box.SIMPLE_HEAD
    return Align.center(table)


def make_est_completion(time_data) -> Align:
    """Some example content."""
    table = Table(show_header=False, show_footer=False,
                  header_style="bold yellow")
    table.add_column()
    table.add_column()
    table.add_row(Text.from_markup("[b yellow]Total Jobs"),
                  str(time_data["total_jobs"]))
    table.add_row(Text.from_markup("[b yellow]Total Batches"),
                  str(time_data["total_batches"]))
    table.add_row(Text.from_markup("[b yellow]Jobs/Batch"),
                  str(time_data["jobs_per_batch"]))
    table.add_row(Text.from_markup("[b yellow]Time/Batch"),
                  str(time_data["time_per_batch"]))
    table.add_row(Text.from_markup("[b yellow]Start Time"),
                  str(time_data["start_time"]))
    table.add_row(Text.from_markup("[b yellow]Est. Stop Time"),
                  str(time_data["stop_time"]))
    table.add_row(Text.from_markup("[b yellow]Est. Duration"),
                  str(time_data["est_duration"]))
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
        "mle run",
        "[b blue]-np, -nw, -resource, -purpose",
        "[b red] Start experiment with .yaml config",
    )
    table.add_row(
        "mle retrieve",
        "[b blue]-e_id, -fig_dir, -exp_dir",
        "[b red] Retrieve results from cluster/GCS",
    )
    table.add_row(
        "mle report",
        "[b blue]--experiment_id",
        "[b red] Generate results .md, .html report",
    )
    table.add_row(
        "mle monitor",
        "[b blue]None",
        "[b red] Monitor resource usage on cluster",
    )
    table.add_row(
        "mle init",
        "[b blue]None",
        "[b red] Initialize credentials/default setup",
    )
    #table.row_styles = ["none", "dim"]
    table.border_style = "white"
    table.box = box.SIMPLE_HEAD
    return table


def make_cpu_util_plot(cpu_hist) -> Align:
    """ Plot curve displaying a CPU usage times series for the cluster. """
    x = np.arange(len(cpu_hist["rel_cpu_util"]))
    y = np.array(cpu_hist["rel_cpu_util"])

    fig = tpl.figure()
    fig.plot(x, y, xlabel="Time", width=40, height=10,
             ylim=[-0.1, 1.1])
    plot_str = fig.get_string()
    plot_str = plot_str[:-61] + "                   Time"
    message = Table.grid()
    message.add_column(no_wrap=True)
    message.add_row(plot_str,)
    return Align.center(message)


def make_memory_util_plot(mem_hist) -> Align:
    """ Plot curve displaying a memory usage times series for the cluster. """
    x = np.arange(len(mem_hist["rel_mem_util"]))
    y = np.array(mem_hist["rel_mem_util"])

    fig = tpl.figure()
    fig.plot(x, y, xlabel="Time", width=40, height=10,
             ylim=[-0.1, 1.1], label="% Util.")
    plot_str = fig.get_string()
    plot_str = plot_str[:-61] + "                   Time"
    message = Table.grid()
    message.add_column(no_wrap=True)
    message.add_row(plot_str,)
    return Align.center(message)


def update_dashboard(layout, resource, util_hist):
    """ Helper function that fills dashboard with life!"""
    # Get newest data depending on resourse!
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    if resource == "sge-cluster":
        user_data = get_user_sge_data()
        host_data = get_host_sge_data()
        util_data = get_utilisation_sge_data()
    total_data = get_total_experiments(db, all_experiment_ids)
    last_data = get_last_experiment(db, all_experiment_ids[-1])
    time_data = get_time_experiment(db, all_experiment_ids[-1])

    # Add utilisation data to storage dictionaries
    util_hist["timestamps"].append(util_data["timestamp"])
    util_hist["total_mem"] = util_data["mem"]
    util_hist["rel_mem_util"].append(util_data["mem_util"]/util_data["mem"])
    util_hist["total_cpu"] = util_data["cores"]
    util_hist["rel_cpu_util"].append(util_data["cores_util"]/util_data["cores"])

    # Limit memory to approx. last 27 hours
    util_hist["timestamps"] = util_hist["timestamps"][:100000]
    util_hist["rel_mem_util"] = util_hist["rel_mem_util"][:100000]
    util_hist["rel_cpu_util"] = util_hist["rel_cpu_util"][:100000]

    # Fill the left-main with life!
    layout["l-box1"].update(Panel(make_user_jobs(user_data),
                                  border_style="red",
                                  title="Scheduled Jobs by User",))
    layout["l-box2"].update(Panel(make_node_jobs(host_data),
                                  border_style="red",
                                  title="Running Jobs by Node",))

    # Fill the center-main with life!
    layout["center"].update(Panel(make_protocol(),
                                  border_style="bright_blue",
                                 title="Experiment Protocol Summary",))

    # Fill the right-main with life!
    layout["r-box1"].update(Panel(make_total_experiments(total_data),
                                  border_style="yellow",
                            title="Total Number of Experiment Runs",))
    layout["r-box2"].update(Panel(make_last_experiment(last_data),
                                  border_style="yellow",
                            title="Last Experiment Configuration",))
    layout["r-box3"].update(Panel(make_est_completion(time_data),
                                  border_style="yellow",
                    title="Est. Experiment Completion Time",))

    # Fill the footer with life!
    layout["f-box1"].update(Panel(make_cpu_util_plot(util_hist),
                    title=(f"CPU - Total: {int(util_data['cores'])}T"
                           + f" | Start: {util_hist['timestamps'][0]}"),
                    border_style="red"),)
    layout["f-box2"].update(Panel(make_memory_util_plot(util_hist),
                    title=(f"Mem - Total: {int(util_data['mem'])}G"),
                    border_style="red"))
    layout["f-box3"].update(Panel(make_help_commands(),
                                  border_style="white",
                title="[b white]Help: Core MLE-Toolbox CLI Commands",))
    return layout, util_hist


def cluster_dashboard():
    """ Initialize and update rich dashboard with cluster data. """
    # Get host resource [local, sge-cluster, slurm-cluster]
    resource = determine_resource()
    util_hist = {"rel_mem_util": [], "rel_cpu_util": [], "timestamps": []}

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
    layout, util_hist = update_dashboard(layout, resource, util_hist)

    # Start timer for GCS pulling of protocol db
    start_t = time.time()
    # Run the live updating of the dashboard
    with Live(layout, refresh_per_second=10, screen=True):
        while True:
            layout, util_hist = update_dashboard(layout, resource, util_hist)
            # Every 10 minutes pull the newest DB from GCS
            if time.time() - start_t > 600:
                if cc.general.use_gcloud_protocol_sync:
                    accessed_remote_db = get_gcloud_db()
                start_t = time.time()
            time.sleep(1)
