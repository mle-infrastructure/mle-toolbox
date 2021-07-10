from mle_toolbox import mle_config
from .startup_script import sge_base_job_config, sge_job_exec


def sge_generate_startup_file(job_arguments: dict) -> str:
    """ Generate the bash script template to submit with qsub. """
    # Set the job template depending on the desired number of GPUs
    base_template = (sge_base_job_config + '.')[:-1]

    # Add desired number of requested gpus
    if "num_gpus" in job_arguments:
        if job_arguments["num_gpus"] > 0:
            base_template += '#$ -l cuda="{num_gpus}(RTX2080)" \n'

    # Exclude specific nodes from the queue
    if "exclude_nodes" in job_arguments:
        base_template += ('#$ -l hostname=' + '&'.join(('!'
                          + f'{x}' + mle_config.sge.info.node_extension
                          for x in job_arguments['exclude_nodes'])) + '\n')

    # Only run on specific nodes from the queue
    if "include_nodes" in job_arguments:
        base_template += ('#$ -l hostname=' + '&'.join((
                          + f'{x}' + mle_config.sge.info.node_extension
                          for x in job_arguments['include_nodes'])) + '\n')

    # Set the max required memory per job in MB - standardization Slurm
    if "memory_per_job" in job_arguments:
        base_template += "#$ -l h_vmem={memory_per_job}M\n"
        base_template += "#$ -l mem_free={memory_per_job}M\n"

    # Set the max required time per job (afterwards terminate)
    if "time_per_job" in job_arguments:
        base_template += "#$ -l h_rt={time_per_job}\n"

    # Add the return of the job id
    base_template += "#$ -terse\n"

    # Add the 'tail' - script execution to the string
    template_out = base_template + sge_job_exec
    return template_out
