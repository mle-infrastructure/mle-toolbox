import re
import datetime, sys
import subprocess as sp
import numpy as np
from colorclass import Color
from terminaltables import SingleTable
from ..utils import load_mle_toolbox_config


def monitor_slurm_cluster():
    """ Get the resource usage/availability on Slurm cluster. """
    #  squeue -u <user_name>
    cc = load_mle_toolbox_config()
    while True:
        table_data = [
            [Color('{autocyan}ALL{/autocyan}'),
             Color('{autogreen}RUNNING{/autogreen}'),
             Color('{autogreen}WAITING{/autogreen}'),
             Color('{autogreen}COMPLETING{/autogreen}')] +
            [Color('{autoyellow}' + part + '{/autoyellow}')
             for part in cc.slurm.info.partitions]
        ]
        time_t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        table_instance = SingleTable(table_data, 'SLURM Cluster: {} - {}'.format(
            time_t, cc.slurm.credentials.user_name))
        table_instance.inner_heading_row_border = False
        table_instance.inner_row_border = True
        table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}

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
        table_instance.table_data.append([total_jobs, running, waiting,
                                          completing] + per_partition.tolist())
        sys.stdout.write("\r" + table_instance.table)
        sys.stdout.flush()
