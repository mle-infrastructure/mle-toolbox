from datetime import datetime
import subprocess as sp
import numpy as np
from mle_toolbox.utils import load_mle_toolbox_config


cc = load_mle_toolbox_config()


def get_local_data():
    """ Helper to get all utilisation data for local resource. """
    user_data = get_user_local_data()
    host_data = get_host_local_data()
    util_data = get_util_local_data()
    return user_data, host_data, util_data


def get_user_local_data():
    """ Get jobs scheduled by Slurm cluster users. """
    user_data = {"users": [],
                 "total": [],
                 "run": [],
                 "wait": [],
                 "login": []}
    return user_data


def get_host_local_data():
    """ Get jobs running on different Slurm cluster hosts. """
    host_data = {"host_id": [],
                 "total": [],
                 "run": [],
                 "login": []}
    return host_data


def get_util_local_data():
    """ Get memory and CPU utilisation for specific slurm partition. """
    util_data = {"cores": 1,
                 "cores_util": 0,
                 "mem": 1,
                 "mem_util": 0,
                 "time_date": datetime.now().strftime("%m/%d/%y"),
                 "time_hour": datetime.now().strftime("%H:%M:%S")}
    return util_data
