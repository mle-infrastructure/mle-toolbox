from ..experiment import spawn_post_processing_job


def run_post_processing(resource_to_run: str,
                        post_process_args: dict,
                        experiment_dir: str):
    """ Execute job for post processing of previously obtained results. """
    status_out = spawn_post_processing_job(
                resource_to_run=resource_to_run,
                job_filename=post_process_args.process_fname,
                job_arguments=post_process_args.process_job_args,
                experiment_dir=experiment_dir,
                extra_cmd_line_input=post_process_args.extra_cmd_line_input)
    return status_out
