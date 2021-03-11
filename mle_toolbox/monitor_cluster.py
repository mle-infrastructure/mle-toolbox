from .utils import determine_resource
from .monitor import monitor_sge_cluster, monitor_sge_cluster


def main():
    """ Monitor the ressources & running jobs on your cluster. """
    ressource = determine_resource()
    if ressource == "sge-cluster":
        monitor_sge_cluster()
    elif ressource == "slurm-cluster":
        monitor_slurm_cluster()
    else:
        print("You are running your job locally: {}".format(ressource))


if __name__ == "__main__":
    monitor_sge_cluster()
