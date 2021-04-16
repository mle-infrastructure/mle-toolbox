import paramiko
import random
import time
import logging
from datetime import datetime
from typing import Union
import os
import sys, select
from .ssh_transfer import SSH_Manager
from .ssh_session_sge import generate_remote_qsub_str
from .ssh_session_slurm import generate_remote_slurm_str
from ..utils import load_mle_toolbox_config

# Import cluster credentials/settings - SGE or Slurm scheduling system
cc = load_mle_toolbox_config()


def ask_for_resource_to_run():
    """ Ask user if they want to exec on remote resource. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    resource = input(time_t + " Where to run? [local/slurm/sge/gcp] ")
    while resource not in ["local", "slurm", "sge", "gcp"]:
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


def run_remote_experiment(remote_resource: str, exec_config: str,
                          remote_exec_dir: str, purpose: Union[None, str]):
    """ Run the experiment on the remote resource. """
    # 0. Load the toolbox config, setup logger & ssh manager for local2remote
    logger = logging.getLogger(__name__)
    ssh_manager = SSH_Manager(remote_resource)

    # 1. Rsync over the current working dir into remote_exec_dir
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print(f"{time_t} Do you want to sync the remote dir? [Y/N]", end= ' '),
    sys.stdout.flush()
    i, o, e = select.select([sys.stdin], [], [], 30)
    if (i):
        sync = sys.stdin.readline().strip()
    else:
        sync = "N"

    if sync == "Y":
        ssh_manager.sync_dir(os.getcwd(), remote_exec_dir)
        logger.info("Synced local experiment dir with remote dir")

    # 2. Generate and execute bash qsub file
    if remote_resource == "sge-cluster":
        exec_str, random_str, exec_cmd = generate_remote_qsub_str(
                                                    exec_config,
                                                    remote_exec_dir,
                                                    purpose)
        remote_exec_fname = 'qsub_cmd.qsub'
    elif remote_resource == "slurm-cluster":
        exec_str, random_str, exec_cmd = generate_remote_slurm_str(
                                                    exec_config,
                                                    remote_exec_dir,
                                                    purpose)
        remote_exec_fname = 'sbash_cmd.sh'

    ssh_manager.write_to_file(exec_str, remote_exec_fname)
    ssh_manager.execute_command(exec_cmd)
    logger.info(f"Generated & executed {random_str} remote job" +
                f" on {remote_resource}.")

    # 3. Monitor progress & clean up experiment (separate for reconnect!)
    remote_connect_monitor_clean(remote_resource, random_str)


def remote_connect_monitor_clean(remote_resource, random_str):
    """ Reconnect & monitor running job. """
    logger = logging.getLogger(__name__)
    ssh_manager = SSH_Manager(remote_resource)
    # Monitor the experiment
    monitor_remote_job(ssh_manager, random_str)
    logger.info(f"Experiment on {remote_resource} finished.")

    # Delete .qsub gen files
    ssh_manager.delete_file(random_str + ".txt")
    ssh_manager.delete_file(random_str + ".err")
    if remote_resource == "slurm-cluster":
        remote_exec_fname = 'sbash_cmd.sh'
    elif remote_resource == "sge-cluster":
        remote_exec_fname = 'qsub_cmd.qsub'
    ssh_manager.delete_file(remote_exec_fname)
    logger.info(f"Done cleaning up experiment debris.")
    return


terminal_print = 31*"=" + "  EXPERIMENT FINISHED  " + 31*"="
def monitor_remote_job(ssh_manager, random_str: str):
    """ Monitor the remote experiment. """
    file_length, fail_counter = 0, 0
    while True:
        try:
            ssh_manager.get_file(random_str + ".txt", "exp_log.txt")
            temp = open('exp_log.txt', 'r')
            all_lines = temp.readlines()
        except Exception as e:
            if fail_counter == 0:
                print("Couldn't open log .txt file")
            fail_counter += 1
            time.sleep(2)
            continue

        line_diff = len(all_lines) - file_length
        if line_diff > 0:
            for line in all_lines[-line_diff:]:
                print(line, end = '')
            file_length += line_diff
        # Pause a little between monitoring steps
        time.sleep(3)
        # Break out of loop if final line is printed
        if len(all_lines) > 0:
            if all_lines[-1][:-1] == terminal_print:
                break
    os.remove("exp_log.txt")
    return
