from mle_toolbox import mle_config
from dotmap import DotMap
from typing import Union


def check_single_job_args(resource_to_run: str, job_arguments: dict):
    """Check if required args are provided. Complete w. default otw."""
    if resource_to_run == "sge-cluster":
        full_job_arguments = sge_check_job_args(job_arguments)
    elif resource_to_run == "slurm-cluster":
        full_job_arguments = slurm_check_job_args(job_arguments)
    elif resource_to_run == "gcp-cloud":
        full_job_arguments = gcp_check_job_args(job_arguments)
    elif resource_to_run == "local":
        full_job_arguments = local_check_job_args(job_arguments)
    return full_job_arguments


def sge_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    if "env_name" not in job_arguments.keys():
        job_arguments["env_name"] = mle_config.general.remote_env_name

    if "use_conda_venv" not in job_arguments.keys():
        job_arguments["use_conda_venv"] = mle_config.general.use_conda_venv

    if "use_venv_venv" not in job_arguments.keys():
        job_arguments["use_venv_venv"] = mle_config.general.use_venv_venv

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.sge.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v

    return job_arguments


def slurm_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    if "env_name" not in job_arguments.keys():
        job_arguments["env_name"] = mle_config.general.remote_env_name

    if "use_conda_venv" not in job_arguments.keys():
        job_arguments["use_conda_venv"] = mle_config.general.use_conda_venv

    if "use_venv_venv" not in job_arguments.keys():
        job_arguments["use_venv_venv"] = mle_config.general.use_venv_venv

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.slurm.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v
    return job_arguments


def gcp_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.gcp.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v

    return DotMap(job_arguments)


# Default job arguments (if not different supplied)
local_default_job_arguments = {
    "env_name": mle_config.general.remote_env_name,
    "use_conda_venv": mle_config.general.use_conda_venv,
    "use_venv_venv": mle_config.general.use_venv_venv,
}


def local_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """Check the input job arguments & add default values if missing."""
    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in local_default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v
    return job_arguments
