import os
import time
import subprocess as sp
from typing import Union
from .manage_local_job import submit_subprocess, random_id
from ..utils import load_mle_toolbox_config


# Base qsub template
sge_base_job_config = """
#####################################
#!/bin/sh
#$ -binding linear:{num_logical_cores}
#$ -q {queue}
#$ -cwd
#$ -V
#$ -N {job_name}
#$ -e {err_file}.err
#$ -o {log_file}.txt
"""


# Base template for executing .py script
sge_job_exec = """
#####################################
echo "------------------------------------------------------------------------"
. ~/.bashrc && conda activate {env_name}
echo "Successfully activated virtual environment - Ready to start job"
echo "------------------------------------------------------------------------"
echo "Job started on" `date`
echo "------------------------------------------------------------------------"
{script}
echo "------------------------------------------------------------------------"
echo "Job ended on" `date`
echo "------------------------------------------------------------------------"
"""


def sge_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """ Check the input job arguments & add default values if missing. """
    # Load cluster config
    cc = load_mle_toolbox_config()

    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in cc.sge.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v

    # Reformatting of time for SGE qsub - hh:mm:ss but in is dd:hh:mm
    if "time_per_job" in job_arguments.keys():
        days, hours, minutes = job_arguments["time_per_job"].split(":")
        hours_sge = str(int(days) * 24 + int(hours))
        if len(hours_sge) < 2: hours_sge = "0" + hours_sge
        sge_time = hours_sge + ":" + minutes + ":00"
        job_arguments["time_per_job"] = sge_time
    return job_arguments


def sge_generate_remote_job_template(job_arguments: dict):
    """ Generate the bash script template to submit with qsub. """
    # Load cluster config
    cc = load_mle_toolbox_config()

    # Set the job template depending on the desired number of GPUs
    base_template = (sge_base_job_config + '.')[:-1]

    # Add desired number of requested gpus
    if "num_gpus" in job_arguments:
        if job_arguments["num_gpus"] > 0:
            base_template += '#$ -l cuda="{num_gpus}(RTX2080)" \n'

    # Exclude specific nodes from the queue
    if "exclude_nodes" in job_arguments:
        base_template += ('#$ -l hostname=' + '&'.join((f'!' + cc.sge.info.node_reg_exp[0]
                          + f'{x:02}' + cc.sge.info.node_extension
                          for x in job_arguments['exclude_nodes'])) + '\n')

    # Only run on specific nodes from the queue
    if "include_nodes" in job_arguments:
        base_template += ('#$ -l hostname=' + '&'.join(( cc.sge.info.node_reg_exp[0]
                          + '{x:02}' + cc.sge.info.node_extension
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



def sge_submit_remote_job(filename: str,
                          cmd_line_arguments: str,
                          job_arguments: dict,
                          clean_up: bool=True):
    """ Create a qsub job & submit it based on provided file to execute. """
    # Load cluster config
    cc = load_mle_toolbox_config()

    # Create base string of job id
    base = "submit_{0}".format(random_id())

    # Write the desired python code to .py file to execute
    script = "python " + filename + cmd_line_arguments
    job_arguments["script"] = script
    sge_job_template = sge_generate_remote_job_template(job_arguments)

    open(base + '.qsub', 'w').write(sge_job_template.format(**job_arguments))

    # Submit the job via subprocess call
    command = 'qsub < ' + base + '.qsub ' + '&>/dev/null'
    proc = submit_subprocess(command)

    # Wait until system has processed submission
    while True:
        poll = proc.poll()
        if poll is None:
            continue
        else:
            break

    # Get output & error messages (if there is an error)
    out, err = proc.communicate()
    if proc.returncode != 0:
        print(out, err)
        job_id = -1
    else:
        job_info = out.split(b'\n')
        job_id = int(job_info[0].decode("utf-8").split()[0])

    # Wait until the job is listed under the qstat scheduled jobs
    while True:
        try:
            out = sp.check_output(["qstat", "-u", cc.sge.credentials.user_name])
            job_info = out.split(b'\n')[2:]
            running_job_ids = [int(job_info[i].decode("utf-8").split()[0])
                               for i in range(len(job_info) - 1)]
            success = job_id in running_job_ids
            if success:
                break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            time.sleep(0.5)

    # Finally delete all the unneccessary log files
    if clean_up:
        os.remove(base + '.qsub')

    return job_id


def sge_monitor_remote_job(job_id: Union[list, int]):
    """ Monitor the status of a job based on its id. """
    # Load cluster config
    cc = load_mle_toolbox_config()

    fail_counter = 0
    while True:
        try:
            out = sp.check_output(["qstat", "-u", cc.sge.credentials.user_name])
            break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            time.sleep(0.5)
            # fail_counter += 1
            # if fail_counter > 100:
            #     return -1
    job_info = out.split(b'\n')[2:]
    running_job_ids = [int(job_info[i].decode("utf-8").split()[0])
                       for i in range(len(job_info) - 1)]
    if type(job_id) == int:
        job_id = [job_id]
    S1 = set(job_id)
    S2 = set(running_job_ids)
    job_status = len(S1.intersection(S2)) > 0
    return job_status
