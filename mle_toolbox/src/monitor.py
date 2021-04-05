from mle_toolbox.utils import determine_resource
from mle_toolbox.monitor import (cluster_dashboard,
                                 monitor_slurm_cluster)


def monitor():
    """ Monitor the ressources & running jobs on your cluster. """
    resource = determine_resource()
    if resource == "sge-cluster":
        cluster_dashboard()
    elif resource == "slurm-cluster":
        monitor_slurm_cluster()
    else:
        print("You are running your job locally: {}".format(ressource))
