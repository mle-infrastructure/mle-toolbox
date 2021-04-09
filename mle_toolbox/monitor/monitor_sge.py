from datetime import datetime
import subprocess as sp
from mle_toolbox.utils import load_mle_toolbox_config


cc = load_mle_toolbox_config()


def get_user_sge_data():
    """ Get jobs scheduled by Slurm cluster users. """
    user_data = []
    all_users = sp.check_output(['qconf', '-suserl']).split(b'\n')[:-1]
    all_users = [u.decode() for u in all_users]
    user_cmd = [['-u', u] for u in all_users]
    user_cmd = [item for sublist in user_cmd for item in sublist]
    for user in all_users:
        try:
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
                    user_data.append([user, total_jobs, running, qlogins])
        except:
            pass
    return user_data


def get_host_sge_data():
    """ Get jobs running on different SGE cluster hosts. """
    host_data = []
    try:
        all_users = sp.check_output(['qconf', '-suserl']).split(b'\n')[:-1]
        all_users = [u.decode() for u in all_users]
        user_cmd = [['-u', u] for u in all_users]
        user_cmd = [item for sublist in user_cmd for item in sublist]
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
            host_data.append([host_id, total_jobs, running, qlogins])
    except:
        pass
    return host_data


def get_util_sge_data():
    """ Get memory and CPU utilisation for specific SGE queue. """
    all_hosts = sp.check_output(['qconf', '-ss']).split(b'\n')
    all_hosts = [u.decode() for u in all_hosts]
    # Filter list of hosts by node 'stem'
    all_hosts = list(filter(lambda k: cc.sge.info.node_reg_exp[0]
                            in k, all_hosts))

    all_cores, all_cores_util, all_mem, all_mem_util = [], [], [], []
    # Loop over all hosts and collect the utilisation data from the
    # cmd line qhost output
    for host in all_hosts:
        out = sp.check_output(['qhost', '-h', host]).split(b'\n')
        out = [u.decode() for u in out][3].split()
        cores, core_util, mem, mem_util = out[2], out[6], out[7], out[8]
        all_cores.append(float(cores))
        try:
            all_cores_util.append(float(core_util) * float(cores))
        except:
            all_cores_util.append(0)
        all_mem.append(float(mem[:-1]))
        all_mem_util.append(float(mem_util[:-1]))
    return {"cores": sum(all_cores),
            "cores_util": sum(all_cores_util),
            "mem": sum(all_mem),
            "mem_util": sum(all_mem_util),
            "time_date": datetime.now().strftime("%m/%d/%y"),
            "time_hour": datetime.now().strftime("%H:%M:%S")}
