from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.spinner import Spinner

import datetime as dt
import numpy as np
import termplotlib as tpl

from mle_toolbox.utils import (load_mle_toolbox_config,
                               determine_resource)
from mle_toolbox.protocol import (protocol_summary,
                                  generate_protocol_table)


cc = load_mle_toolbox_config()


class Header:
    """ Display header with clock and general toolbox configurations. """
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
    """ Generate rich table summarizing jobs scheduled by users. """
    all_active_users = len(user_data["total"])
    sum_all = str(sum(user_data["total"]))
    sum_running = str(sum(user_data["run"]))
    sum_login = str(sum(user_data["login"]))
    sum_wait = str(sum(user_data["wait"]))

    # Create table with structure with aggregated numbers
    table = Table(show_header=True, show_footer=False,
                  header_style="bold red")
    table.add_column("USER", Text.from_markup("[b]Total", justify="right"),
                     style="white", justify="left")
    table.add_column("ALL", sum_all, justify="center")
    table.add_column("RUN", sum_running, justify="center")
    table.add_column("LOG", sum_login, justify="center")
    table.add_column("W", sum_wait, justify="center")

    # Add row for each individual user
    for u_id in range(all_active_users):
        table.add_row(user_data["user"][u_id],
                      str(user_data["total"][u_id]),
                      str(user_data["run"][u_id]),
                      str(user_data["login"][u_id]),
                      str(user_data["wait"][u_id]))

    table.show_footer = True
    table.row_styles = ["none", "dim"]
    table.border_style = "red"
    table.box = box.SIMPLE
    return Align.center(table)


def make_node_jobs(host_data) -> Align:
    """ Generate rich table summarizing jobs running on different nodes. """
    all_nodes = len(host_data["total"])
    sum_all = str(sum(host_data["total"]))
    sum_running = str(sum(host_data["run"]))
    sum_login = str(sum(host_data['login']))

    table = Table(show_header=True, show_footer=False,
                  header_style="bold red")
    table.add_column("NODE", Text.from_markup("[b]Total", justify="right"),
                     style="white", justify="left")
    table.add_column("ALL", sum_all, justify="center")
    table.add_column("RUN", sum_running, justify="center")
    table.add_column("LOGIN", sum_login, justify="center")

    # Add row for each individual cluster/queue/partition node
    for h_id in range(all_nodes):
        table.add_row(host_data["user"][h_id],
                      str(host_data["total"][h_id]),
                      str(host_data["run"][h_id]),
                      str(host_data["login"][h_id]))

    table.show_footer = True
    table.row_styles = ["none", "dim"]
    table.border_style = "red"
    table.box = box.SIMPLE
    return Align.center(table)


def make_protocol() -> Table:
    """ Generate rich table summarizing experiment protocol summary. """
    df = protocol_summary(tail=29, verbose=False)
    table = generate_protocol_table(df)
    return Align.center(table)


def make_total_experiments(total_data) -> Align:
    """ Generate rich table summarizing all experiments in protocol db. """
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
    """ Generate rich table summarizing last scheduled experiment settings. """
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
    """ Generate rich table summarizing estim. time of experim. completion. """
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
    """ Generate rich table summarizing core toolbox subcommands. """
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
