import os
import time
import subprocess as sp
from typing import Union
from .manage_local_job import submit_subprocess, random_id
from ..utils import load_mle_toolbox_config

# Base qsub template
slurm_base_job_config = """#!/bin/bash
#SBATCH --job-name={job_name}        # job name (not id)
#SBATCH --output={log_file}.txt      # output file
#SBATCH --error={err_file}.err       # error file
#SBATCH --partition={partition}      # partition to submit to
#SBATCH --cpus={num_logical_cores}   # number of cpus
"""


# Base template for executing .py script
slurm_job_exec = """
module load nvidia/cuda/10.0
source ~/miniconda3/etc/profile.d/conda.sh
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
conda deactivate
"""


def slurm_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """ Check the input job arguments & add default values if missing. """
    # Load cluster config
    cc = load_mle_toolbox_config()

    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in cc.slurm.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v

    # Reformatting of time for Slurm SBASH - d-hh:mm but in is dd:hh:mm
    if "time_per_job" in job_arguments.keys():
        days, hours, minutes = job_arguments["time_per_job"].split(":")
        slurm_time = days[1] + "-" + hours + ":" + minutes
        job_arguments["time_per_job"] = slurm_time

    # SGE gives logical cores while Slurm seems to give only threads?!
    if "num_logical_cores" in job_arguments.keys():
        job_arguments["num_logical_cores"] = job_arguments["num_logical_cores"]
    return job_arguments


def slurm_generate_remote_job_template(job_arguments: dict):
    """ Generate the bash script template to submit with SBATCH. """
    # Set the job template depending on the desired number of GPUs
    base_template = (slurm_base_job_config + '.')[:-1]

    # Add desired number of requested gpus
    if "num_gpus" in job_arguments:
        if job_arguments["num_gpus"] > 0:
            base_template += "#SBATCH --gres=gpu:tesla:{num_gpus} \n"

    # Set the max required memory per job
    if "memory_per_cpu" in job_arguments:
        base_template += "#SBATCH --mem-per-cpu={memory_per_job}\n"

    # Set the max required time per job (afterwards terminate)
    if "time_per_job" in job_arguments:
        base_template += "#SBATCH --time={time_per_job}\n"

    # Set the max required memory per job in MB - standardization SGE
    if "memory_per_job" in job_arguments:
        base_template += "#SBATCH --mem={memory_per_job}\n"

    # Add the 'tail' - script execution to the string
    template_out = base_template + slurm_job_exec
    return template_out


def slurm_submit_remote_job(filename: str,
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
    slurm_job_template = slurm_generate_remote_job_template(job_arguments)

    open(base + '.sh', 'w').write(slurm_job_template.format(**job_arguments))

    # Submit the job via subprocess call
    command = 'sbatch < ' + base + '.sh'
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
        job_id = int(out.decode("utf-8").split()[-1])

    # TODO: Add check that status is running!
    # Wait until the job is listed under the qstat scheduled jobs
    while True:
        try:
            out = sp.check_output(["squeue", "-u", cc.slurm.credentials.user_name])
            job_info = out.split(b'\n')[1:]
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
        os.remove(base + '.sh')

    return job_id


def slurm_monitor_remote_job(job_id: Union[list, int]):
    """ Monitor the status of a job based on its id. """
    # Load cluster config
    cc = load_mle_toolbox_config()
    #fail_counter = 0
    while True:
        try:
            out = sp.check_output(["squeue", "-u", cc.slurm.credentials.user_name])
            break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            time.sleep(0.5)
            # fail_counter += 1
            # if fail_counter > 100:
            #     return -1

    job_info = out.split(b'\n')[1:]
    running_job_ids = [int(job_info[i].decode("utf-8").split()[0])
                       for i in range(len(job_info) - 1)]
    if type(job_id) == int:
        job_id = [job_id]
    S1 = set(job_id)
    S2 = set(running_job_ids)
    job_status = len(S1.intersection(S2)) > 0
    return job_status
