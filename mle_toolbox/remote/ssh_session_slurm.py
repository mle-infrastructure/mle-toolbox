import os
from typing import Union
from mle_toolbox import mle_config

save_cmd_to_exec = "echo '{srun_str}' > ./{session_name}"
screen_launch = "screen -d -m -S {session_name}"
screen_send = (
    "screen -S {session_name} -p 0 -X stuff "
    "'srun --partition standard --time=5-00:00"
    " --cpus 1 --pty bash ./{session_name}^M'"
)

# For slurm we need to store executable file
srun_pre = ". ~/.bash_profile && . ~/.bashrc && "

enable_conda = "conda activate {remote_env_name} && "
enable_venv = "source {}/{}/bin/activate && "

# Execute experiment and log output to file with base config .yaml fname
srun_post = (
    "chmod a+rx {exec_dir} && "
    "cd {exec_dir} && "
    "mle run {exec_config} {purpose_str} --no_welcome "
    "2>&1 | tee ~/{session_name}.txt"
)


def generate_remote_slurm_cmd(
    exec_config: str, exec_dir: str, purpose: Union[None, str]
):
    """Generate srun exec file for this experiment."""
    # Name tmux session based on experiment .yaml config name
    base, fname_and_ext = os.path.split(exec_config)
    session_name, ext = os.path.splitext(fname_and_ext)

    # Purpose string to add to experiment
    purpose_str = f"-p {purpose}" if purpose is not None else "-np"

    # Copy the exec string over into home directory
    if mle_config.general.use_conda_virtual_env:
        srun_str = (
            srun_pre
            + enable_conda.format(remote_env_name=mle_config.general.remote_env_name)
            + srun_post.format(
                exec_dir=exec_dir,
                exec_config=exec_config,
                purpose_str=purpose_str,
                session_name=session_name,
            )
        )
    else:
        srun_str = (
            srun_pre
            + enable_venv.format(
                os.environ["WORKON_HOME"], mle_config.general.remote_env_name
            )
            + srun_post.format(
                exec_dir=exec_dir,
                exec_config=exec_config,
                purpose_str=purpose_str,
                session_name=session_name,
            )
        )

    cmds_to_exec = [
        save_cmd_to_exec.format(srun_str=srun_str, session_name=session_name),
        screen_launch.format(session_name=session_name),
        screen_send.format(session_name=session_name),
    ]
    return session_name, cmds_to_exec
