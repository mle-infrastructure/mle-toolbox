import sys
import logging
import argparse
from datetime import datetime
from os.path import expanduser


__version__ = "0.2.2"


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
    print(time_t, f"Thx for using MLE-Toolbox {__version__} Locally, on SGE, Slurm or GCP")
    if verbose:
        print(time_t, "It implements the following experiment types:")
        print("    - single-experiment: Run a single configuration experiment.")
        print("    - multiple-experiments: Run multiple configs & random seeds.")
        print("    - hyperparameter-search: Run a hyperparameter search (Grid, Random, SMBO).")


def get_mle_args():
    """ Get config file path & other ingredients """
    parser = argparse.ArgumentParser()
    parser.add_argument('config_fname', metavar='C', type=str,
                        default="experiment_config.yaml",
                        help ='Filename to load config yaml from')
    parser.add_argument('-d', '--debug', default=False, action='store_true',
                        help ='Run simulation in debug mode')
    parser.add_argument('-p', '--purpose', default=None, nargs='+',
                        help ='Purpose of the experiment to run')
    parser.add_argument('-np', '--no_protocol', default=False,
                        action='store_true',
                        help ='Run simulation in without protocol recording')
    parser.add_argument('-del', '--delete_after_upload', default=False,
                        action='store_true',
                        help ='Delete results after upload to GCloud.')
    parser.add_argument('-nw', '--no_welcome', default=False,
                        action='store_true',
                        help ='Do not print welcome message.')
    parser.add_argument('-reconnect', '--remote_reconnect', default=None,
                        help ='Reconnect to experiment by str name.')
    parser.add_argument('-resource', '--remote_resource', default=None,
                        help ='Resource to run experiment on.')

    # Allow CLI to change base train fname/config .json/experiment dir
    parser.add_argument('-train_fname', '--base_train_fname', default=None,
                        help ='Python script to run exp on.')
    parser.add_argument('-train_config', '--base_train_config', default=None,
                        help ='Base config file to load and modify.')
    parser.add_argument('-exp_dir', '--experiment dir', default=None,
                        help ='Experiment directory.')
    return parser.parse_args()


def prepare_logger(experiment_dir: str, debug_mode: bool=False):
    """ Setup up the verbose/file logging of the experiment. """
    logger = logging.getLogger()
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    file_path = (os.path.join(experiment_dir, "exp_debug.log")
                 if debug_mode else expanduser("~/full_debug.log"))
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
