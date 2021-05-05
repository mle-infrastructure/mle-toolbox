from typing import Union

def gcp_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """ Check the input job arguments & add default values if missing. """
    raise NotImplementedError


def gcp_submit_job(filename: str,
                   cmd_line_arguments: str,
                   job_arguments: dict,
                   clean_up: bool=True):
    """ Create a GCP VM job & submit it based on provided file to execute. """
    raise NotImplementedError


def gcp_monitor_job(vm_name: Union[list, int]) -> bool:
    """ Monitor the status of a job based on its VM name. """
    raise NotImplementedError
