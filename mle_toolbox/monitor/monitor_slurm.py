import subprocess as sp
import numpy as np
from mle_toolbox.utils import load_mle_toolbox_config


cc = load_mle_toolbox_config()


def get_user_slurm_data():
    user_data = None
    return user_data


def get_host_slurm_data():
    host_data = None
    return host_data


def get_util_slurm_data():
    util_data = None
    return util_data


def monitor_slurm_cluster():
    """ Get the resource usage/availability on Slurm cluster. """
    #  squeue -u <user_name>
    all_job_infos = []
    try:
        processes = sp.check_output(['squeue', '-u', cc.slurm.credentials.user_name])
        all_job_infos = processes.split(b'\n')[1:-1]
        all_job_infos = [j.decode() for j in all_job_infos]
    except:
        pass

    total_jobs = len(all_job_infos)
    per_partition = np.zeros(len(cc.slurm.info.partitions)).astype(int)
    running, waiting, completing = 0, 0, 0
    for job in all_job_infos:
        job_clean = job.split()
        job_partition = job_clean[1]
        job_status = job_clean[4]
        running += (job_status == 'R')
        waiting += (job_status == 'PD')
        completing += (job_status == 'CG')
        for i, part in enumerate(cc.slurm.info.partitions):
            if job_partition == part:
                per_partition[i] += 1

    # Add a row for the user of interest
    data = [total_jobs, running, waiting, completing] + per_partition.tolist()
    return data
