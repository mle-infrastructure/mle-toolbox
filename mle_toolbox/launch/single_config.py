from mle_scheduler import MLEJob
from mle_toolbox import check_single_job_args


def run_single_config(
    resource_to_run: str,
    meta_job_args: dict,
    single_job_args: dict,
    debug_mode: bool = False,
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
        resource_to_run=resource_to_run,
        job_filename=meta_job_args["base_train_fname"],
        job_arguments=single_job_args,
        config_filename=meta_job_args["base_train_config"],
        experiment_dir=meta_job_args["experiment_dir"],
        debug_mode=debug_mode,
    )
    # 2. Run the single experiment
    _ = experiment.run()
