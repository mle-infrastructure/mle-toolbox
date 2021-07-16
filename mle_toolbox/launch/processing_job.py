from ..experiment import spawn_processing_job


def run_processing_job(
    resource_to_run: str, processing_args: dict, experiment_dir: str
):
    """Execute job for post processing of previously obtained results."""
    status_out = spawn_processing_job(
        resource_to_run=resource_to_run,
        job_filename=processing_args.processing_fname,
        job_arguments=processing_args.processing_job_args,
        experiment_dir=experiment_dir,
        extra_cmd_line_input=processing_args.extra_cmd_line_input,
    )
    return status_out