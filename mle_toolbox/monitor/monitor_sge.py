import re
import datetime, sys
import subprocess as sp
import numpy as np
from colorclass import Color
from terminaltables import SingleTable
from .utils import load_mle_toolbox_config


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
