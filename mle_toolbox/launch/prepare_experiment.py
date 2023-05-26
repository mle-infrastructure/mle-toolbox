import os
import sys
import logging
from datetime import datetime
from rich.table import Table
from rich.panel import Panel
from rich.console import Console


def welcome_to_mle_toolbox() -> None:
    """Display header with clock and general toolbox configurations."""
    welcome_ascii = """    __  _____    ______   ______            ____
   /  |/  / /   / ____/  /_  __/___  ____  / / /_  ____  _  __
  / /|_/ / /   / __/______/ / / __ \/ __ \/ / __ \/ __ \| |/_/
 / /  / / /___/ /__/_____/ / / /_/ / /_/ / / /_/ / /_/ />  <
/_/  /_/_____/_____/    /_/  \____/\____/_/_.___/\____/_/|_|
    """.splitlines()

    grid = Table.grid(expand=True)
    grid.add_column(justify="left")
    grid.add_column(justify="right")
    grid.add_row(
        welcome_ascii[0],
        datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    )
    grid.add_row(
        welcome_ascii[1],
        # "  [link=https://tinyurl.com/srpy4nrp]You are awesome![/link] [not italic]:hugging_face:[/]",
        "  You are awesome! [not italic]:hugging_face:[/]",
    )

    grid.add_row(
        welcome_ascii[2],
        # "  [link=https://twitter.com/RobertTLange]@RobertTLange[/link] :bird:",
        "  @RobertTLange :bird:",
    )
    grid.add_row(
        welcome_ascii[3],
        # "  [link=https://roberttlange.github.io/mle-toolbox/]MLE-Toolbox Docs[/link] [not italic]:notebook:[/]",
        "  MLE-Toolbox Docs [not italic]:notebook:[/]",
    )
    grid.add_row(
        welcome_ascii[4],
        # "  [link=https://github.com/RobertTLange/mle-toolbox/]MLE-Toolbox Repo[/link] [not italic]:pencil:[/]",
        "  MLE-Toolbox Repo [not italic]:pencil:[/]",
    )
    panel = Panel(grid, style="white on blue", expand=True)
    console = Console(width=87)
    console.print(panel)


def prepare_logger() -> logging.Logger:
    """Setup up the verbose/file logging of the experiment."""
    logger = logging.getLogger()
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # Always log to root directory
    file_path = os.path.expanduser("~/full_debug.log")
    logging.basicConfig(
        filename=file_path,
        filemode="a",
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        datefmt="%m/%d/%Y %I:%M:%S %p",
        level=logging.DEBUG,
    )
    logging.getLogger("git").setLevel(logging.ERROR)
    logging.getLogger("google").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("scp").setLevel(logging.CRITICAL)
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)
    logging.getLogger("sshtunnel").setLevel(logging.CRITICAL)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def check_experiment_config(job_config: dict) -> None:
    """Check if config has all necessary ingredients for job to run."""
    # Compile list of required arguments for specific job types
    necessary_ingredients = ["meta_job_args", "single_job_args"]
    if job_config.meta_job_args["experiment_type"] == "multiple-configs":
        necessary_ingredients += ["multi_config_args"]
    elif job_config.meta_job_args["experiment_type"] == "hyperparameter-search":
        necessary_ingredients += ["param_search_args"]
    elif job_config.meta_job_args["experiment_type"] == "population-based-training":
        necessary_ingredients += ["pbt_args"]

    # Check if ingredients are in config keys
    for nec_ing in necessary_ingredients:
        if nec_ing not in job_config.keys():
            raise ValueError(f"Provide additional input: {nec_ing}")

    # TODO: Make this more robust by asserting existence of required keys
    # Differentiate between required and not - check types and file existence
    """
    meta_job_args: project_name, experiment_type, base_train_fname, base_train_config,
                   experiment_dir, (remote_exec_dir) = all strings, check files
    single_job_args: job_name, num_logical_cores, log_file, err_file, env_name,
                     extra_cmd_line_input (all optional - except env_name?)
    multi_config_args: config_fnames, num_seeds, random_seeds
    param_search_args: search_logging, search_resources, search_config
    """
    # If random seeds are not explicitly provided - set to None
    if job_config.meta_job_args["experiment_type"] == "multiple-configs":
        if "random_seeds" not in job_config["multi_config_args"].keys():
            job_config["multi_config_args"]["random_seeds"] = None
    elif job_config.meta_job_args["experiment_type"] == "hyperparameter-search":
        if (
            "random_seeds"
            not in job_config["param_search_args"]["search_resources"].keys()
        ):
            job_config["param_search_args"]["search_resources"]["random_seeds"] = None
    return job_config
