import re
import datetime, sys
import subprocess as sp
import numpy as np
from colorclass import Color
from terminaltables import SingleTable
from .utils import determine_resource, load_mle_toolbox_config


def main():
    """ Monitor the ressources & running jobs on your cluster. """
    ressource = determine_resource()
    if ressource == "sge-cluster":
        monitor_sge_cluster()
    elif ressource == "slurm-cluster":
        monitor_slurm_cluster()
    else:
        print("You are running your job locally: {}".format(ressource))


def monitor_sge_cluster():
    """ Get the resource usage/availability on SunGridEngine cluster. """
    cc = load_mle_toolbox_config()
    while True:
        try:
            table_data = [
                [Color('{autored}USER{/autored}'), Color('{autocyan}ALL{/autocyan}'),
                 Color('{autogreen}RUNNING{/autogreen}'), Color('{autoyellow}QLOGIN{/autoyellow}')]
            ]
            time_t = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            table_instance = SingleTable(table_data, 'SGE Cluster: {}'.format(time_t))
            table_instance.inner_heading_row_border = False
            table_instance.inner_row_border = True
            table_instance.justify_columns = {0: 'center', 1: 'center', 2: 'center'}

            #----------------------------------------------------------------------#
            # Get all users & check if they running jobs
            #----------------------------------------------------------------------#
            all_users = sp.check_output(['qconf', '-suserl']).split(b'\n')[:-1]
            all_users = [u.decode() for u in all_users]
            user_cmd = [['-u', u] for u in all_users]
            user_cmd = [item for sublist in user_cmd for item in sublist]
            for user in all_users:
                queue_all = len(sp.check_output(['qstat', '-u', user, '-q',
                                                 cc.sge.info.queue]).split(b'\n')[:-1])
                if queue_all != 0: queue_all -= 2

                queue_spare = len(sp.check_output(['qstat', '-u', user, '-q',
                                                   cc.sge.info.spare]).split(b'\n')[:-1])
                if queue_spare != 0: queue_spare -= 2
                total_jobs = queue_all + queue_spare

                if total_jobs != 0:
                    qlogins, running = 0, 0
                    if queue_spare != 0:
                        ps = sp.Popen(('qstat', '-u', user, '-q',
                                       cc.sge.info.spare), stdout=sp.PIPE)
                        try:
                            qlogins = sp.check_output(('grep', 'QLOGIN'), stdin=ps.stdout)
                            ps.wait()
                            qlogins = len(qlogins.split(b'\n')[:-1])
                        except:
                            pass

                    if queue_all != 0:
                        running = len(sp.check_output(['qstat', '-s', 'r', '-u', user, '-q',
                                                       cc.sge.info.queue]).split(b'\n')[:-1])
                        if running != 0: running -= 2
                    # Add a row for each user that has running jobs
                    if qlogins + running != 0:
                        table_instance.table_data.append([user, total_jobs,
                                                          running, qlogins])

            #----------------------------------------------------------------------#
            # Get all hosts & check if they have running jobs on them
            #----------------------------------------------------------------------#
            table_instance.table_data.append([Color('{autored}NODES{/autored}'), "-----",
                                              "-----", "-----"])
            for host_id in cc.sge.info.node_ids:
                queue_all, queue_spare = 0, 0
                qlogins, running = 0, 0
                cmd = ['qstat', '-q', cc.sge.info.queue] + user_cmd
                ps = sp.Popen(cmd, stdout=sp.PIPE)
                try:
                    queue_all = sp.check_output(('grep', cc.sge.info.node_reg_exp[0] + host_id),
                                                stdin=ps.stdout)
                    ps.wait()
                    queue_all = len(queue_all.split(b'\n')[:-1])
                except:
                    pass

                cmd = ['qstat', '-q', cc.sge.info.spare] + user_cmd
                ps = sp.Popen(cmd, stdout=sp.PIPE)
                try:
                    queue_spare = sp.check_output(('grep', cc.sge.info.node_reg_exp[0] + host_id),
                                                  stdin=ps.stdout)
                    ps.wait()
                    # print(queue_spare)
                    queue_spare = len(queue_spare.split(b'\n')[:-1])
                except:
                    pass

                if queue_all != 0:
                    cmd = ['qstat', '-s', 'r', '-q', cc.sge.info.queue] + user_cmd
                    ps = sp.Popen(cmd, stdout=sp.PIPE)
                    try:
                        running = sp.check_output(('grep', cc.sge.info.node_reg_exp[0] + host_id),
                                                    stdin=ps.stdout)
                        ps.wait()
                        running = len(running.split(b'\n')[:-1])
                    except:
                        pass

                if queue_spare != 0:
                    cmd = ['qstat', '-s', 'r', '-q', cc.sge.info.spare] + user_cmd
                    ps = sp.Popen(cmd, stdout=sp.PIPE)
                    try:
                        qlogins = sp.check_output(('grep', cc.sge.info.node_reg_exp[0] + host_id),
                                                    stdin=ps.stdout)
                        ps.wait()
                        qlogins = len(qlogins.split(b'\n')[:-1])
                    except:
                        pass

                # TODO: Figure out double grep and why only my jobs are found
                total_jobs = running + qlogins
                # Add a row for each host in the SGE cluster
                table_instance.table_data.append([host_id, total_jobs, running, qlogins])

            sys.stdout.write("\r" + table_instance.table)
            sys.stdout.flush()
        except:
            pass
        #print(table_instance.table, end="\r", flush=True)



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
        table_instance = SingleTable(table_data, 'SLURM Cluster: {} - {}'.format(time_t,
                                                                                 cc.slurm.credentials.user_name))
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


if __name__ == "__main__":
    monitor_sge_cluster()
