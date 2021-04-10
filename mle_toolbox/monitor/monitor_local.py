from datetime import datetime
import subprocess as sp
import numpy as np
from mle_toolbox.utils import load_mle_toolbox_config


cc = load_mle_toolbox_config()


def get_local_data():
    """ Helper to get all utilisation data for local resource. """
    try:
        import psutil
    except:
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError(f"{err}. You need to install `psutil` "
                                      "to monitor local machine resources.")
    user_data = get_local_process_data()
    host_data = get_local_core_data()
    util_data = get_util_local_data()
    return user_data, host_data, util_data


def get_local_process_data():
    """ Get jobs scheduled by local machine. """
    user_data = {"users": [],
                 "total": [],
                 "run": [],
                 "wait": [],
                 "login": []}
    return user_data


def get_local_core_data():
    """ Get utilization per core. """
    # psutil.pids()
    # psutil.cpu_percent(percpu=True)
    host_data = {"host_id": [],
                 "total": [],
                 "run": [],
                 "login": []}
    return host_data


def get_util_local_data():
    """ Get memory and CPU utilisation for specific local machine. """
    num_cpus = psutil.cpu_count()
    total_mem = psutil.virtual_memory()._asdict()["total"]/1000000000
    used_mem = psutil.virtual_memory()._asdict()["used"]/1000000000
    util_data = {"cores": num_cpus,
                 "cores_util": num_cpus*psutil.cpu_percent()/100,
                 "mem": total_mem,
                 "mem_util": used_mem,
                 "time_date": datetime.now().strftime("%m/%d/%y"),
                 "time_hour": datetime.now().strftime("%H:%M:%S")}
    return util_data
