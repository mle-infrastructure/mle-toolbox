import paramiko
import random
import time
import logging
from datetime import datetime
from typing import Union
import os
import sys, select
from .ssh_transfer import SSH_Manager
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
        exec_str, random_str, exec_cmd = generate_remote_qsub_str(exec_config,
                                                    remote_exec_dir, purpose)
        remote_exec_fname = 'qsub_cmd.qsub'
    elif remote_resource == "slurm-cluster":
        exec_str, random_str, exec_cmd = generate_remote_slurm_str(exec_config,
                                                    remote_exec_dir, purpose)
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


qsub_pre = """
#!/bin/bash
#$ -q cognition-all.q
#$ -cwd
#$ -V
#$ -N {random_str}
#$ -e {random_str}.err
#$ -o {random_str}.txt
. ~/.bashrc
. /etc/profile
"""

qsub_post = """
chmod a+rx {exec_dir}
cd {exec_dir}
run-experiment {exec_config} {purpose_str} --no_welcome
"""
# #$ -l hostname=cognition12.ml.tu-berlin.de
# Problem with source not found
enable_conda = ('/bin/bash -c "source $(conda info --base)/etc/profile.d/conda.sh"'
                ' && conda activate {remote_env_name}')
enable_venv = '/bin/bash -c "source {}/{}/bin/activate"'


def generate_remote_qsub_str(exec_config: str, exec_dir: str,
                             purpose: Union[None, str]):
    """ Generate qsub exec file for this experiment. """
    random_str = "q" + str(random.randint(0, 10000))
    purpose_str = f"-p {purpose}" if purpose is not None else f"-np"

    # Copy the exec string over into home directory
    if cc.general.use_conda_virtual_env:
        qsub_str = (qsub_pre.format(random_str=random_str) +
                    enable_conda.format(
                        remote_env_name=cc.general.remote_env_name) +
                    qsub_post.format(exec_dir=exec_dir,
                                     exec_config=exec_config,
                                     purpose_str=purpose_str))
    else:
        qsub_str = (qsub_pre.format(random_str=random_str) +
                    enable_venv.format(
                        os.environ['WORKON_HOME'],
                        cc.general.remote_env_name) +
                    qsub_post.format(exec_dir=exec_dir,
                                     exec_config=exec_config,
                                     purpose_str=purpose_str))

    pre_cmd = """
    . ~/.bash_profile;
    . ~/.bashrc;
    PATH=$PATH:/opt/ge/bin/lx-amd64;
    export SGE_ROOT=/opt/ge
    """
    exec_cmd = pre_cmd + "qsub < qsub_cmd.qsub &>/dev/null"
    return qsub_str, random_str, exec_cmd


slurm_pre = """#!/bin/bash
#SBATCH --job-name={random_str}        # job name (not id)
#SBATCH --output={random_str}.txt      # output file
#SBATCH --error={random_str}.err       # error file
#SBATCH --partition=standard           # partition to submit to
#SBATCH --cpus=2                       # number of cpus
#SBATCH --time=10-00:00                # Running time experiment (max 10 days)
module load nvidia/cuda/10.0
"""

slurm_pre = """
chmod a+rx {exec_dir}
cd {exec_dir}
run-experiment {exec_config} {purpose_str} --no_welcome
"""


def generate_remote_slurm_str(exec_config: str, exec_dir: str,
                              purpose: Union[None, str]):
    """ Generate qsub exec file for this experiment. """
    random_str = "s" + str(random.randint(0, 10000))
    purpose_str = f"-p {purpose}" if purpose is not None else f"-np"

    # Copy the exec string over into home directory
    if cc.general.use_conda_virtual_env:
        qsub_str = (slurm_pre.format(random_str=random_str) +
                    enable_conda.format(
                        remote_env_name=cc.general.remote_env_name) +
                    slurm_post.format(exec_dir=exec_dir,
                                      exec_config=exec_config,
                                      purpose_str=purpose_str))
    else:
        qsub_str = (slurm_pre.format(random_str=random_str) +
                    enable_venv.format(
                        os.environ['WORKON_HOME'],
                        cc.general.remote_env_name) +
                    slurm_post.format(exec_dir=exec_dir,
                                      exec_config=exec_config,
                                      purpose_str=purpose_str))

    pre_cmd = """
    . ~/.bash_profile;
    . ~/.bashrc;
    """
    exec_cmd = pre_cmd + "sbatch < sbash_cmd.sh &>/dev/null"
    return slurm_str, random_str, exec_cmd


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
