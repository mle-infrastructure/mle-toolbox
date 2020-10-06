import logging
from datetime import datetime
from os.path import expanduser
import mle_toolbox.cluster_config as cc


__version__ == 0.2.0


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

    ch = logging.StreamHandler()
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
    elif job_config.meta_job_args["job_type"] == "population-based-training":
        raise ValueError("Provide a valid job type")
        # necessary_ingredients = ["pbt_args"]

    # Check if ingredients are in config keys
    for nec_ing in necessary_ingredients:
        if nec_ing not in job_config.keys():
            raise ValueError("Provide additional input: {}".format(nec_ing))
