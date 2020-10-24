import paramiko
import random
import time
import logging
from datetime import datetime
from typing import Union
import os
from scp import SCPClient
from ..utils import load_mle_toolbox_config
from .ssh_transfer import createSSHClient


def ask_for_remote_resource():
    """ Ask user if they want to exec on remote resource. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    resource = input(time_t + " Where to run? [local/slurm/sge/gcp] ")
    while resource_to_run not in ["local", "slurm", "sge", "gcp"]:
        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        resource = input(time_t + " Please repeat: [local/slurm/sge/gcp] ")

    if resource == "local":
        resource_to_run = "local"
    elif resource == "slurm":
        resource_to_run = "slurm-cluster"
    elif resource == "sge":
        resource_to_run = "sge-cluster"
    elif resurce == "gcp":
        resource_to_run = "gcp-cloud"
    return resource_to_run


def run_remote_experiment(remote_resource, exec_config,
                          remote_exec_dir, purpose):
    """ Run the experiment on the remote resource. """
    # TODO: Clean solution for tunneling - ssh class?!
    # TODO: Differentiate between resources - sge/slurm/gcloud
    # TODO: Add port to use to mle config
    # TODO: Add a reconnect option if connection breaks

    # 0. Load the toolbox config & setup logger for local2remote
    cc = load_mle_toolbox_config()
    logger = logging.getLogger(__name__)

    if remote_resource == "sge-cluster":
        server = cc.sge.info.main_server_name
        user = cc.sge.credentials.user_name
        password = cc.sge.credentials.password
        port = cc.sge.info.ssh_port
    else:
        raise NotImplementedError

    # 1. Rsync over the current working dir into remote_exec_dir
    sync_dir_2_remote(remote_exec_dir, server, user, password)
    logger.info("Synced local experiment dir with remote dir")

    # 2. Generate and execute bash qsub file
    random_str = generate_remote_meta_qsub(exec_config, remote_exec_dir,
                                           purpose, server, user, password)
    execute_remote_meta_qsub(server, user, password)
    logger.info(f"Generated & exec'd meta remote job on {remote_resource}.")

    # 3. Monitor the experiment
    monitor_remote_meta_qsub(random_str, server, user, password)
    logger.info(f"Experiment on {remote_resource} finished.")

    # 4. Delete .qsub gen files
    clean_up_remote_meta_qsub(random_str, server, user, password)
    logger.info(f"Done cleaning up experiment debris.")


def sync_dir_2_remote(remote_exec_dir: str, server: str, user: str,
                      password: str, port: int=22):
    """ Sync cwd to remote exec dir. """
    cwd = os.getcwd()
    ssh = createSSHClient(server, user, password, port)
    scp = SCPClient(ssh.get_transport())
    scp.put(cwd, remote_exec_dir, recursive=True)


qsub_cmd = """
#!/bin/sh
#$ -l hostname=cognition12.ml.tu-berlin.de
#$ -q cognition-all.q
#$ -cwd
#$ -V
#$ -N {random_str}
#$ -e {random_str}.err
#$ -o {random_str}.txt
. ~/.bashrc && conda activate mle-toolbox
chmod a+rx {exec_dir}
cd {exec_dir}
run-experiment {exec_config} {purpose_str} --no_welcome
"""

def generate_remote_meta_qsub(exec_config: str,
                              exec_dir: str,
                              purpose: Union[None, str],
                              server: str, user: str,
                              password: str, port: int=22):
    """ Generate qsub exec file for this experiment. """
    ssh = createSSHClient(server, user, password, port)
    random_str = "q" + str(random.randint(0, 10000))
    purpose_str = f"-p {purpose}" if purpose is not None else f"-np"

    # Copy the exec string over into home directory
    ftp = ssh.open_sftp()
    file = ftp.file('qsub_cmd.qsub', "w", -1)
    file.write(qsub_cmd.format(random_str=random_str, exec_dir=exec_dir,
                               exec_config=exec_config,
                               purpose_str=purpose_str))
    file.flush()
    ftp.close()
    ssh.close()
    return random_str


def execute_remote_meta_qsub(server: str, user: str,
                             password: str, port: int=22):
    """ Execute qsub exec file for this experiment. """
    # TODO: Make this more general! - So far only for SGE/Sprekeler setup!
    pre_cmd = """
    . ~/.bash_profile;
    . ~/.bashrc;
    PATH=$PATH:/opt/ge/bin/lx-amd64;
    export SGE_ROOT=/opt/ge
    """
    ssh = createSSHClient(server, user, password, port)
    cmd = "qsub < qsub_cmd.qsub &>/dev/null"
    stdin, stdout, stderr = ssh.exec_command(pre_cmd + cmd, get_pty=True)


terminal_print = 31*"=" + "  EXPERIMENT FINISHED  " + 31*"="
def monitor_remote_meta_qsub(random_str: str, server: str, user: str,
                             password: str, port: int=22):
    """ Monitor & print most recent output of experiment. """
    # Repeatedly check the output .txt & print the difference
    ssh = createSSHClient(server, user, password, port)
    sftp_client = ssh.open_sftp()
    file_length, fail_counter = 0, 0
    while True:
        try:
            remote_file = sftp_client.open(random_str + ".txt")
        except:
            if fail_counter == 0:
                print("Couldn't open log .txt file")
                fail_counter += 1
            time.sleep(2)
            continue

        all_lines = []
        try:
            for line in list(remote_file):
                all_lines.append(line)
        finally:
            remote_file.close()

        line_diff = len(all_lines) - file_length
        if line_diff > 0:
            for line in all_lines[-line_diff:]:
                print(line, end = '')
            file_length += line_diff
        # Pause a little between monitoring steps
        time.sleep(2)
        # Break out of loop if final line is printed
        if len(all_lines) > 0:
            if all_lines[-1][:-1] == terminal_print:
                break
    return


def clean_up_remote_meta_qsub(random_str: str, server: str, user: str,
                              password: str, port: int=22):
    """ Delete the meta output file creates through qsub """
    ssh = createSSHClient(server, user, password, port)
    sftp_client = ssh.open_sftp()
    # Remove .qsub exec & results
    sftp_client.remove(random_str + ".txt")
    sftp_client.remove(random_str + ".err")
    sftp_client.remove("qsub_cmd.qsub")
