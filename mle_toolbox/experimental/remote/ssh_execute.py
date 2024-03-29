import time
import logging
from datetime import datetime
from typing import Union
import os
import sys
import select
from mle_toolbox import mle_config
from mle_scheduler.ssh import SSH_Manager
from .ssh_session_sge import generate_remote_sge_cmd
from .ssh_session_slurm import generate_remote_slurm_cmd


def run_remote_experiment(
    remote_resource: str,
    exec_config: str,
    remote_exec_dir: str,
    purpose: Union[None, str],
):
    """Run the experiment on the remote resource."""
    # 0. Load the toolbox config, setup logger & ssh manager for local2remote
    logger = logging.getLogger(__name__)
    if remote_resource == "slurm-cluster":
        resource = "slurm"
    elif remote_resource == "sge-cluster":
        resource = "sge"
    ssh_manager = SSH_Manager(
        user_name=mle_config[resource].credentials.user_name,
        pkey_path=mle_config.general.pkey_path,
        main_server=mle_config[resource].info.main_server_name,
        jump_server=mle_config[resource].info.jump_server_name,
        ssh_port=mle_config[resource].info.ssh_port,
    )

    # 1. Rsync over the current working dir into remote_exec_dir
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print(f"{time_t} Do you want to sync the remote dir? [Y/N]", end=" ")
    sys.stdout.flush()
    i, o, e = select.select([sys.stdin], [], [], 30)
    if i:
        sync = sys.stdin.readline().strip()
    else:
        sync = "N"

    if sync == "Y":
        ssh_manager.sync_dir(os.getcwd(), remote_exec_dir)
        logger.info("Synced local experiment dir with remote dir")

    # 2. Generate and execute bash qsub file
    if remote_resource == "sge-cluster":
        session_name, exec_cmds = generate_remote_sge_cmd(
            exec_config, remote_exec_dir, purpose
        )
    elif remote_resource == "slurm-cluster":
        session_name, exec_cmds = generate_remote_slurm_cmd(
            exec_config, remote_exec_dir, purpose
        )

    ssh_manager.execute_command(exec_cmds)
    logger.info(f"Generated & executed remote job on {remote_resource}.")
    logger.info(f"Attach to the screen session via " f"`screen -r {session_name}`.")

    # 3. Monitor progress & clean up experiment (separate for reconnect!)
    time.sleep(10)
    monitor_remote_session(ssh_manager, session_name)


def monitor_remote_session(ssh_manager: SSH_Manager, session_name: str):
    """Monitor the remote experiment."""
    logger = logging.getLogger(__name__)

    # Monitor the experiment
    terminal_print = 31 * "=" + "  EXPERIMENT FINISHED  " + 31 * "="
    file_length, fail_counter = 0, 0
    while True:
        try:
            ssh_manager.get_file(f"{session_name}.txt", f"{session_name}.txt")
            temp = open(f"{session_name}.txt", "r")
            all_lines = temp.readlines()
        except Exception:
            if fail_counter == 0:
                print("Couldn't open log .txt file")
            fail_counter += 1
            time.sleep(2)
            continue

        line_diff = len(all_lines) - file_length
        if line_diff > 0:
            for line in all_lines[-line_diff:]:
                print(line, end="")
            file_length += line_diff
        # Pause a little between monitoring steps
        time.sleep(3)
        # Break out of loop if final line is printed
        if len(all_lines) > 0:
            if all_lines[-1][:-1] == terminal_print:
                break

    # Delete the log file
    os.remove(f"{session_name}.txt")
    logger.info(f"Experiment on {ssh_manager.remote_resource} finished.")
    return
