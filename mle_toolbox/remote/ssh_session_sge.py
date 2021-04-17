import os
from typing import Union
from mle_toolbox import mle_config

screen_launch = "screen -d -m -S {session_name}"
screen_send = "screen -S {session_name} -p 0 -X stuff '"
qrsh_pre = ("""qrsh -N {session_name} " """
            """. ~/.bash_profile && . ~/.bashrc && """
            """PATH=$PATH:/opt/ge/bin/lx-amd64 && """
            """export SGE_ROOT=/opt/ge && """)


enable_conda = """conda activate {remote_env_name} && """
enable_venv = """source {}/{}/bin/activate && """


# Execute experiment and log output to file with base config .yaml fname
qrsh_post = ("""chmod a+rx {exec_dir} && """
             """cd {exec_dir} && """
             """mle run {exec_config} {purpose_str} --no_welcome """
             """2>&1 | tee {session_name}.txt"^M'""")


def generate_remote_sge_cmd(exec_config: str,
                            exec_dir: str,
                            purpose: Union[None, str]):
    """ Generate qrsh exec file for this experiment. """
    # Name tmux session based on experiment .yaml config name
    base, fname_and_ext = os.path.split(exec_config)
    session_name, ext = os.path.splitext(fname_and_ext)

    # Purpose string to add to experiment
    purpose_str = f"-p {purpose}" if purpose is not None else f"-np"

    # Copy the exec string over into home directory
    if mle_config.general.use_conda_virtual_env:
        qrsh_cmd = (screen_send.format(session_name=session_name) +
                    qrsh_pre.format(session_name=session_name) +
                    enable_conda.format(
                        remote_env_name=mle_config.general.remote_env_name) +
                    qrsh_post.format(exec_dir=exec_dir,
                                     exec_config=exec_config,
                                     purpose_str=purpose_str,
                                     session_name=session_name))
    else:
        qrsh_cmd = (screen_send.format(session_name=session_name) +
                    qrsh_pre.format(session_name=session_name) +
                    enable_venv.format(
                        os.environ['WORKON_HOME'],
                        mle_config.general.remote_env_name) +
                    qrsh_post.format(exec_dir=exec_dir,
                                     exec_config=exec_config,
                                     purpose_str=purpose_str,
                                     session_name=session_name))

    cmds_to_exec = [screen_launch.format(session_name=session_name),
                    qrsh_cmd]
    return session_name, cmds_to_exec
