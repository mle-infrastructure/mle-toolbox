import random
import string
import subprocess as sp
from typing import Union


# Default job arguments (if not different supplied) - TBC
local_default_job_arguments = {'job_name': 'temp',
                               'log_file': 'log',
                               'err_file': 'err'}


def local_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """ Check the input job arguments & add default values if missing. """
    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in local_default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v
    return job_arguments


def submit_local_job(filename: str,
                     cmd_line_arguments: str,
                     job_arguments: dict):
    """ Create a local job & submit it based on provided file to execute. """
    cmd = "python " + filename + cmd_line_arguments
    proc = submit_subprocess(cmd)
    return proc


def submit_subprocess(cmd: str):
    """ Submit a subprocess & return the process. """
    while True:
        try:
            proc = sp.Popen(cmd, shell=True,
                            stdout=sp.PIPE,
                            stderr=sp.PIPE)
            break
        except:
            continue
    return proc


def random_id(length: int=8):
    """ Sample a random string to use for job id. """
    return ''.join(random.sample(string.ascii_letters + string.digits, length))
