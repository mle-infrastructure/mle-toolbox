import os
import time
import subprocess as sp
from typing import Union
from .manage_job_local import submit_subprocess, random_id
from .cluster.slurm.helpers_launch_slurm import slurm_generate_startup_file
from mle_toolbox import mle_config


def slurm_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.slurm.default_job_arguments.items():
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


def slurm_submit_job(
    filename: str, cmd_line_arguments: str, job_arguments: dict, clean_up: bool = True
) -> str:
    """Create a qsub job & submit it based on provided file to execute."""
    # Create base string of job id
    base = "submit_{0}".format(random_id())

    # Write the desired python/bash execution to slurm job submission file
    f_name, f_extension = os.path.splitext(filename)
    if f_extension == ".py":
        script = f"python {filename} {cmd_line_arguments}"
    elif f_extension == ".sh":
        script = f"bash {filename} {cmd_line_arguments}"
    else:
        raise ValueError(
            f"Script with {f_extension} cannot be handled"
            " by mle-toolbox. Only base .py, .sh experiments"
            " are so far implemented. Please open an issue."
        )
    job_arguments["script"] = script
    slurm_job_template = slurm_generate_startup_file(job_arguments)

    open(base + ".sh", "w").write(slurm_job_template.format(**job_arguments))

    # Submit the job via subprocess call
    command = "sbatch < " + base + ".sh"
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
            out = sp.check_output(
                ["squeue", "-u", mle_config.slurm.credentials.user_name]
            )
            job_info = out.split(b"\n")[1:]
            running_job_ids = [
                int(job_info[i].decode("utf-8").split()[0])
                for i in range(len(job_info) - 1)
            ]
            success = job_id in running_job_ids
            if success:
                break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            print(stderr, return_code)
            time.sleep(0.5)

    # Finally delete all the unneccessary log files
    if clean_up:
        os.remove(base + ".sh")

    return job_id


def slurm_monitor_job(job_id: Union[list, int]) -> bool:
    """Monitor the status of a job based on its id."""
    while True:
        try:
            out = sp.check_output(
                ["squeue", "-u", mle_config.slurm.credentials.user_name]
            )
            break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            print(stderr, return_code)
            time.sleep(0.5)

    job_info = out.split(b"\n")[1:]
    running_job_ids = [
        int(job_info[i].decode("utf-8").split()[0]) for i in range(len(job_info) - 1)
    ]
    if type(job_id) == int:
        job_id = [job_id]
    S1 = set(job_id)
    S2 = set(running_job_ids)
    job_status = len(S1.intersection(S2)) > 0
    return job_status
