from .utils import determine_resource
from .monitor import monitor_sge_cluster, monitor_sge_cluster


def main():
    """ Monitor the ressources & running jobs on your cluster. """
    resource = determine_resource()
    if resource == "sge-cluster":
        monitor_sge_cluster()
    elif resource == "slurm-cluster":
        monitor_slurm_cluster()
    else:
        print("You are running your job locally: {}".format(ressource))


if __name__ == "__main__":
    monitor_sge_cluster()
