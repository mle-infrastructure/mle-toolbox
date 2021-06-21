import os
import sys
import logging
from datetime import datetime
from typing import Union
from .. import __version__, mle_config
from ..protocol import protocol_summary, load_local_protocol_db
from ..remote.gcloud_transfer import get_gcloud_db


def welcome_to_mle_toolbox(verbose=False):
    """ Let's friendly greet the next user of the MLE-Toolbox! """
    print(85*"=")
    welcome_ascii = """
            __  _____    ______   ______            ____
           /  |/  / /   / ____/  /_  __/___  ____  / / /_  ____  _  __
          / /|_/ / /   / __/______/ / / __ \/ __ \/ / __ \/ __ \| |/_/
         / /  / / /___/ /__/_____/ / / /_/ / /_/ / / /_/ / /_/ />  <
        /_/  /_/_____/_____/    /_/  \____/\____/_/_.___/\____/_/|_|
    """
    print(welcome_ascii)
    print(72*" " + "@RobertTLange")
    print(85*"=")
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print(time_t, f"Thx for using MLE-Toolbox {__version__}"
                  f" Locally, on Clusters or Cloud.")
    if verbose:
        print(time_t, "It implements the following experiment types:")
        print("  - single-experiment: Run a single configuration experiment.")
        print("  - multiple-experiments: Run multiple configs & random seeds.")
        print("  - hyperparameter-search: Run a hyperparameter search.")


def prepare_logger(experiment_dir: Union[str, None]=None,
                   debug_mode: bool=False):
    """ Setup up the verbose/file logging of the experiment. """
    logger = logging.getLogger()
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    file_path = (os.path.join(experiment_dir, "exp_debug.log")
                 if debug_mode else os.path.expanduser("~/full_debug.log"))
    logging.basicConfig(filename=file_path,
                        filemode='a',
                        format='%(asctime)s %(name)s %(levelname)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        level=logging.DEBUG)
    logging.getLogger("git").setLevel(logging.ERROR)
    logging.getLogger("google").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("scp").setLevel(logging.CRITICAL)
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)
    logging.getLogger("sshtunnel").setLevel(logging.CRITICAL)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt='%(asctime)s %(message)s',
                                  datefmt='%m/%d/%Y %I:%M:%S %p')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def check_job_config(job_config: dict):
    """ Check if config has all necessary ingredients for job to run. """
    # Compile list of required arguments for specific job types
    necessary_ingredients = ["meta_job_args", "single_job_args"]
    if job_config.meta_job_args["job_type"] == "multiple-experiments":
        necessary_ingredients += ["multi_experiment_args"]
    elif job_config.meta_job_args["job_type"] == "hyperparameter-search":
        necessary_ingredients += ["param_search_args"]

    # Check if ingredients are in config keys
    for nec_ing in necessary_ingredients:
        if nec_ing not in job_config.keys():
            raise ValueError("Provide additional input: {}".format(nec_ing))

    # TODO: Make this more robust by asserting existence of required keys
    # Differentiate between required and not - check types and file existence
    """
    meta_job_args: project_name, job_type, base_train_fname,  base_train_config,
                   experiment_dir, (remote_exec_dir) = all strings, check files
    single_job_args: job_name, num_logical_cores, log_file, err_file, env_name,
                     extra_cmd_line_input (all optional - except env_name?)
    multi_experiment_args: config_fnames, num_seeds
    param_search_args: search_logging, search_resources, search_config
    """


def ask_for_experiment_id(repeated_question: bool=False):
    """ Helper function asking user for experiment id from protocol log. """
    # Get most recent/up-to-date experiment DB from Google Cloud Storage
    if not repeated_question:
        if mle_config.general.use_gcloud_protocol_sync:
            accessed_remote_db = get_gcloud_db()
        else:
            accessed_remote_db = False
        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        if accessed_remote_db:
            print(time_t,
                  "Successfully pulled latest experiment protocol from gcloud.")
        else:
            print(time_t, "Careful - you are using local experiment protocol.")
    else:
        accessed_remote_db = False

    # Load in the locally stored experiment protocol DB
    db, all_experiment_ids, _ = load_local_protocol_db()

    # Print the last 10 experiments
    if not repeated_question:
        protocol_summary(tail=10)

    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    if not repeated_question:
        experiment_id = input(time_t + " Which experiment id do you " +
                              "want to use? [E-ID/N]:  ")
    else:
        experiment_id = input(time_t + " Which experiment id do you " +
                              "want to use next? [E-ID/N]:  ")

    while True:
        if experiment_id == "N":
            break

        if experiment_id[:5] != "e-id-":
            experiment_id = "e-id-" + experiment_id

        if experiment_id not in all_experiment_ids:
            print(time_t, "The provided experiment id does not exist")
            experiment_id = input(time_t + " Which experiment did you mean?")
        else:
            break
    return experiment_id, db, all_experiment_ids, accessed_remote_db
