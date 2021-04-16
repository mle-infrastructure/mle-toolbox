import os
from ..utils import load_mle_toolbox_config
# Import cluster credentials/settings - SGE or Slurm scheduling system
cc = load_mle_toolbox_config()


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


def generate_remote_slurm_str(exec_config: str,
                              exec_dir: str,
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
