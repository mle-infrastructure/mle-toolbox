from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel

from mle_toolbox.protocol import load_local_protocol_db
from mle_toolbox.monitor.components import (Header,
                                            make_user_jobs,
                                            make_node_jobs,
                                            make_protocol,
                                            make_total_experiments,
                                            make_last_experiment,
                                            make_est_completion,
                                            make_help_commands,
                                            make_cpu_util_plot,
                                            make_memory_util_plot)
from mle_toolbox.monitor.monitor_sge import (get_user_sge_data,
                                             get_host_sge_data,
                                             get_utilisation_sge_data)
from mle_toolbox.monitor.monitor_db import (get_total_experiments,
                                            get_time_experiment,
                                            get_last_experiment)

"""
TODOS:
- Make qstat calls more efficient/robust -> Faster at startup
- Add data collection functions for slurm, local + gcp!
- Link Author @RobertTLange to twitter account
"""

console = Console()


def layout_mle_dashboard() -> Layout:
    """ Define the MLE-Toolbox `monitor` base dashboard layout."""
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

    # Fill the header with life!
    layout["header"].update(Header())
    return layout


def update_mle_dashboard(layout, resource, util_hist):
    """ Helper function that fills dashboard with life!"""
    # Get newest data depending on resourse!
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    # Get resource dependent data
    if resource == "sge-cluster":
        user_data = get_user_sge_data()
        host_data = get_host_sge_data()
        util_data = get_utilisation_sge_data()

    # Get resource independent data
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
