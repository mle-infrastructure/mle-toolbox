from mle_scheduler import MLEJob
from mle_toolbox import check_single_job_args


def run_single_config(
    resource_to_run: str, meta_job_args: dict, single_job_args: dict
) -> None:
    """
    Run a single experiment locally, remote or in cloud.

    Instantiates `Experiment` class and launches a job. Function call then
    waits until the job is completed and monitors it in a while loop.

    Args:
        resource_to_run (str): Specifies resource to launch job on.
        meta_job_args (dict): Python file, config json and results directory.
        single_job_args (dict): Resources, environment and log file names.

    """
    # 0. Check if all required args are given - otw. add default to copy
    single_job_args = check_single_job_args(resource_to_run, single_job_args.copy())
    # 1. Instantiate the experiment class
    experiment = MLEJob(
        resource_to_run,
        meta_job_args["base_train_fname"],
        single_job_args,
        meta_job_args["base_train_config"],
        meta_job_args["experiment_dir"],
    )
    # 2. Run the single experiment
    _ = experiment.run()
