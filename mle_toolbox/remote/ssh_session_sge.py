import os
from typing import Union
from mle_toolbox import mle_config


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
enable_conda = ('/bin/bash -c'
                '"source $(conda info --base)/etc/profile.d/conda.sh"'
                ' && conda activate {remote_env_name}')
enable_venv = '/bin/bash -c "source {}/{}/bin/activate"'


def generate_remote_sge_str(exec_config: str,
                            exec_dir: str,
                            purpose: Union[None, str]):
    """ Generate qsub exec file for this experiment. """
    random_str = "q" + str(random.randint(0, 10000))
    purpose_str = f"-p {purpose}" if purpose is not None else f"-np"

    # Copy the exec string over into home directory
    if mle_config.general.use_conda_virtual_env:
        qsub_str = (qsub_pre.format(random_str=random_str) +
                    enable_conda.format(
                        remote_env_name=mle_config.general.remote_env_name) +
                    qsub_post.format(exec_dir=exec_dir,
                                     exec_config=exec_config,
                                     purpose_str=purpose_str))
    else:
        qsub_str = (qsub_pre.format(random_str=random_str) +
                    enable_venv.format(
                        os.environ['WORKON_HOME'],
                        mle_config.general.remote_env_name) +
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
