from ..job import Job


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
    # 1. Instantiate the experiment class
    experiment = Job(
        resource_to_run,
        meta_job_args["base_train_fname"],
        meta_job_args["base_train_config"],
        single_job_args,
        meta_job_args["experiment_dir"],
    )
    # 2. Run the single experiment
    _ = experiment.run()
