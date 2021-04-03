import datetime as dt
import time
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
- Make qstat calls a lot more efficient -> Faster at startup
- Get all CPU slots occupied, memory used, GPU usage? -> ask Dom
- Figure out how to store data in time series plots -> Moving average
- Add support for slurm, local, gcp!
- Add documentation/function descriptions
- Link Author @RobertTLange to twitter account
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
            else "\u2022 GCS Sync Protocol: [red]:x:",
            Header.welcome_ascii[1],
            "Author: @RobertTLange :bird:",
            # TODO: Figure out why link won't work if we use text != url
            #[u white link=https://twitter.com/RobertTLange]
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
    table.add_column(":construction:")
    table.add_column("E-ID")
    table.add_column("Date")
    table.add_column("Project")
    table.add_column("Purpose")
    table.add_column("Type")
    table.add_column(":steam_locomotive:", justify="center")
    table.add_column("#Jobs", justify="center")
    table.add_column("#CPU", justify="center")
    table.add_column("#GPU", justify="center")
    table.add_column(":seedling:", justify="center")
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
            status = "[red]:x:"
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


def get_total_experiments(db, all_experiment_ids):
    """ Get data from db to show in 'total_experiments' panel. """
    run, done, aborted, sge, slurm, gcp, local = 0, 0, 0, 0, 0, 0, 0
    report_gen, gcs_stored, retrieved = 0, 0, 0
    for e_id in all_experiment_ids:
        status = db.dget(e_id, "job_status")
        # Job status
        run += status == "running"
        done += status == "completed"
        aborted += status not in ["running", "completed"]
        # Execution resource data
        resource = db.dget(e_id, "exec_resource")
        sge += resource == "sge-cluster"
        slurm += resource == "slurm-cluster"
        gcp += resource == "gcp-cloud"
        local += resource not in ["sge-cluster", "slurm-cluster", "gcp-cloud"]
        # Additional data: Report generated, GCS stored, Results retrieved
        try:
            report_gen += db.dget(e_id, "report_generated")
            gcs_stored += db.dget(e_id, "stored_in_gcloud")
            retrieved += db.dget(e_id, "retrieved_results")
        except:
            pass
    # Return results dictionary
    results = {"run": str(run), "done": str(done), "aborted": str(aborted),
               "sge": str(sge), "slurm": str(slurm), "gcp": str(gcp),
               "local": str(local), "report_gen": str(report_gen),
               "gcs_stored": str(gcs_stored),"retrieved": str(retrieved)}
    return results


def make_total_experiments() -> Align:
    """Some example content."""
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    total_data = get_total_experiments(db, all_experiment_ids)

    table = Table(show_header=False, show_footer=False,
                  header_style="bold yellow")
    table.add_column()
    table.add_column()
    table.add_column()
    table.add_column()
    table.add_row("[b yellow]Total", Spinner('dots', style="magenta"),
                  "[green]:heavy_check_mark:", "[red]:x:")
    table.add_row(str(len(all_experiment_ids)), total_data["run"],
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


def get_last_experiment(db, last_experiment_id):
    """ Get data from db to show in 'last_experiments' panel. """
    # Return results dictionary
    e_path = db.dget(last_experiment_id, "exp_retrieval_path")
    meta_args = db.dget(last_experiment_id, "meta_job_args")
    job_spec_args = db.dget(last_experiment_id, "job_spec_args")
    e_type = meta_args["job_type"]
    e_dir = meta_args["experiment_dir"]
    e_script = meta_args["base_train_fname"]
    e_config = os.path.split(meta_args["base_train_config"])[1]
    results = {"e_dir": e_dir,
               "e_type": e_type,
               "e_script": e_script,
               "e_config": e_config,
               "report_gen": meta_args["report_generation"]}

    # Add additional data based on the experiment type
    if e_type == "hyperparameter-search":
        results["search_type"] = job_spec_args["search_type"]
        results["eval_metrics"] = job_spec_args["eval_metrics"]
        results["params_to_search"] = job_spec_args["params_to_search"]
    elif e_type == "multiple-experiments":
        results["config_fnames"] = job_spec_args["config_fnames"]
    return results


def make_last_experiment() -> Align:
    """Some example content."""
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    last_data = get_last_experiment(db, all_experiment_ids[-1])
    table = Table(show_header=False, show_footer=False,
                  header_style="bold yellow")
    table.add_column()
    table.add_column()
    table.add_row(Text.from_markup("[b yellow]E-ID"),
                  str(last_experiment_id),)
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


def get_time_experiment(db, last_experiment_id):
    """ Get data from db to show in 'time_experiment' panel. """
    meta_args = db.dget(last_experiment_id, "meta_job_args")
    job_spec_args = db.dget(last_experiment_id, "job_spec_args")
    single_job_args = db.dget(last_experiment_id, "single_job_args")

    if meta_args["job_type"] == "hyperparameter-search":
        total_jobs = (job_spec_args["num_search_batches"]
                      * job_spec_args["num_iter_per_batch"]
                      * job_spec_args["num_evals_per_iter"])
        total_batches = job_spec_args["num_search_batches"]
        jobs_per_batch = (job_spec_args["num_iter_per_batch"]
                          * job_spec_args["num_evals_per_iter"])
    elif meta_args["job_type"] == "multiple-experiments":
        total_jobs = (len(job_spec_args["config_fnames"])*
                      job_spec_args["num_seeds"])
        total_batches = 1
        jobs_per_batch = "-"
    else:
        total_jobs = 1
        total_batches = 1
        jobs_per_batch = "-"

    start_time = db.dget(last_experiment_id, "start_time")

    if "time_per_job" in single_job_args.keys():
        time_per_batch = single_job_args["time_per_job"]
        days, hours, minutes = time_per_batch.split(":")
        hours_add, tot_mins = divmod(total_batches * int(minutes), 60)
        days_add, tot_hours = divmod(total_batches * int(hours)+hours_add, 24)
        tot_days = total_batches * int(days) + days_add
        tot_days, tot_hours, tot_mins = (str(tot_days), str(tot_hours),
                                         str(tot_mins))
        if len(tot_days) < 2: tot_days = "0" + tot_days
        if len(tot_hours) < 2: tot_hours = "0" + tot_hours
        if len(tot_mins) < 2: tot_mins = "0" + tot_mins
        est_duration = tot_days + ":" + tot_hours + ":" + tot_mins

        # Check if last experiment has already terminated!
        try:
            stop_time = db.dget(last_experiment_id, "stop_time")
        except:
            start_date = dt.datetime.strptime(start_time, "%m/%d/%Y %H:%M:%S")
            end_date = start_date + dt.timedelta(days=int(tot_days),
                                                 hours=int(tot_hours),
                                                 minutes=int(tot_mins))
            stop_time = end_date.strftime("%m/%d/%Y %H:%M:%S")
    else:
        time_per_batch = "-"
        est_stop_time = "-"
        est_duration = "-"

    results = {"total_jobs": total_jobs,
               "total_batches": total_batches,
               "jobs_per_batch": jobs_per_batch,
               "time_per_batch": time_per_batch,
               "start_time": start_time,
               "stop_time": stop_time,
               "est_duration": est_duration}
    return results


def make_est_completion() -> Align:
    """Some example content."""
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    time_data = get_time_experiment(db, all_experiment_ids[-1])
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


def make_cpu_util_plot() -> Align:
    """ Plot curve displaying a CPU usage times series for the cluster. """
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
    """ Plot curve displaying a memory usage times series for the cluster. """
    x = np.linspace(0, 2 * np.pi, 10)
    y = np.cos(x)

    fig = tpl.figure()
    fig.plot(x, y, xlabel="Time", width=40, height=10)
    plot_str = fig.get_string()
    message = Table.grid()
    message.add_column(no_wrap=True)
    message.add_row(plot_str,)
    return Align.center(message)


def update_dashboard(layout):
    """ Helper function that fills dashboard with life!"""
    # Fill the left-main with life!
    layout["l-box1"].update(Panel(make_user_jobs(), border_style="red",
                                title="Scheduled Jobs by User",))
    layout["l-box2"].update(Panel(make_node_jobs(), border_style="red",
                                title="Running Jobs by Node",))

    # Fill the center-main with life!
    layout["center"].update(Panel(make_protocol(),
                                  border_style="bright_blue",
                                 title="Experiment Protocol Summary",))

    # Fill the right-main with life!
    layout["r-box1"].update(Panel(make_total_experiments(),
                                  border_style="yellow",
                            title="Total Number of Experiment Runs",))
    layout["r-box2"].update(Panel(make_last_experiment(),
                                  border_style="yellow",
                            title="Last Experiment Configuration",))
    layout["r-box3"].update(Panel(make_est_completion(),
                                  border_style="yellow",
                    title="Est. Experiment Completion Time",))

    # Fill the footer with life!
    layout["f-box1"].update(Panel(make_cpu_util_plot(),
                                  title="Total CPU Utilisation",
                                  border_style="red"),)
    layout["f-box2"].update(Panel(make_memory_util_plot(),
                                  title="Total Memory Utilisation",
                                  border_style="red"))
    layout["f-box3"].update(Panel(make_help_commands(),
                                  border_style="white",
                title="[b white]Help: Core MLE-Toolbox CLI Commands",))
    return layout


def monitor_sge_cluster():
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
    layout = update_dashboard(layout)

    # Start timer for GCS pulling of protocol db
    start_t = time.time()
    # Run the live updating of the dashboard
    with Live(layout, refresh_per_second=10, screen=True):
        while True:
            layout = update_dashboard(layout)
            # Every 10 minutes pull the newest DB from GCS
            if time.time() - start_t > 600:
                if cc.general.use_gcloud_protocol_sync:
                    accessed_remote_db = get_gcloud_db()
                start_t = time.time()
            time.sleep(1)
