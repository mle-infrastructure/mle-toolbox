import os
import argparse
from datetime import datetime

from .utils import print_framed
from .remote.ssh_transfer import SSH_Manager
from .remote.gcloud_transfer import send_gcloud_db, get_gcloud_zip_experiment
from .src.prepare_experiment import ask_for_experiment_id


# Get experiment id to retrieve from cmd
def get_retrieve_args():
    """ Get inputs from cmd line """
    parser = argparse.ArgumentParser()
    parser.add_argument('-e_id', '--experiment_id', type=str,
                        default="no-id-given",
                        help ='Experiment ID')
    parser.add_argument('-all_new', '--retrieve_all_new', default=False,
                        action='store_true', help ='Retrieve all new results.')
    parser.add_argument('-fig_dir', '--figures_dir', default=False,
                        action='store_true',
                        help ='Retrieve only subdir containing figures.')
    parser.add_argument('-exp_dir', '--experiment_dir', default=False,
                        action='store_true',
                        help ='Retrieve entire experiment dir.')
    parser.add_argument('-local', '--retrieve_local', default=False,
                        action='store_true',
                        help ='Retrieve experiment dir from remote directory.')
    return parser.parse_args()


def main():
    """ Copy over experiment results folder from cluster. """
    # Get inputs from commandline
    cmd_args = get_retrieve_args()
    experiment_id = cmd_args.experiment_id
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    # Either get entire result dir or only generated figures - ask for input
    if cmd_args.figures_dir:
        get_dir_or_fig = "fig-dir"
    elif cmd_args.experiment_dir:
        get_dir_or_fig = "exp-dir"
    else:
        get_dir_or_fig = input(time_t + " Retrieve entire result dir or " +
                               "only figures? [exp-dir/fig-dir]  ")

    # Retrieve results for a single experiment
    if not cmd_args.retrieve_all_new:
        retrieval_counter = 0
        while True:
            # If no id given show last experiments & ask for input
            if experiment_id == "no-id-given" and retrieval_counter == 0:
                experiment_id, db, all_experiment_ids, accessed_remote_db = ask_for_experiment_id()
                if cmd_args.retrieve_local:
                    retrieve_single_experiment(db, experiment_id,
                                               get_dir_or_fig,
                                               all_experiment_ids)
                else:
                    get_gcloud_zip_experiment(db, experiment_id,
                                              all_experiment_ids)
                retrieval_counter += 1
            else:
                experiment_id, _, _, _ = ask_for_experiment_id(True)
                if experiment_id == "N":
                    break
                if cmd_args.retrieve_local:
                    retrieve_single_experiment(db, experiment_id,
                                               get_dir_or_fig,
                                               all_experiment_ids)
                else:
                    get_gcloud_zip_experiment(db, experiment_id,
                                              all_experiment_ids)
                retrieval_counter += 1
    else:
        list_of_new_e_ids = []
        for e_id in all_experiment_ids:
            completed = (db.dget(e_id, "job_status") == "completed")
            not_retrieved_yet = not db.dget(e_id, "retrieve_results")
            if completed and not_retrieved_yet:
                list_of_new_e_ids.append(e_id)

        for i, experiment_id in enumerate(list_of_new_e_ids):
            try:
                stored_in_gcloud = db.dget(e_id, "stored_in_gcloud")
            except:
                stored_in_gcloud = False
            # Pull either from remote machine or gcloud bucket
            if cmd_args.retrieve_local and not stored_in_gcloud:
                retrieve_single_experiment(db, experiment_id,
                                           get_dir_or_fig,
                                           all_experiment_ids)
            else:
                get_gcloud_zip_experiment(db, experiment_id,
                                          all_experiment_ids)
            print_framed(f'COMPLETED E-ID {i+1}/{len(list_of_new_e_ids)}')

    if accessed_remote_db:
        send_gcloud_db()
        print(time_t, "Updated retrieval protocol status & \
              send to gcloud storage.")


def retrieve_single_experiment(db, experiment_id: str,
                               get_dir_or_fig: str,
                               all_experiment_ids: list):
    # Try to retrieve experiment path from protocol db
    while True:
        if get_dir_or_fig == "exp-dir":
            # Get path to experiment results dir & get cluster to retrieve from
            file_path = db.dget(experiment_id, "exp_retrieval_path")
            break
        elif get_dir_or_fig == "fig-dir":
            # Get path to figure dir & get cluster to retrieve from
            dir_path = db.dget(experiment_id, "exp_retrieval_path")
            fig_name = db.dget(experiment_id, "figures_dir")
            file_path = os.path.join(dir_path, fig_name)
            break
        else:
            get_dir_or_fig = input(time_t + " Please repeat your " +
                                   "input: [exp-dir/fig-dir]  ")

    remote_resource = db.dget(experiment_id, "exec_resource")
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print(time_t, "{} - Started retrieving {} - from {}".format(experiment_id,
                                                file_path, remote_resource))

    # Create SSH & SCP client - Pull files into new dir by name of exp-id
    if remote_resource in ["sge-cluster", "slurm-cluster"]:
        ssh_manager = SSH_Manager(remote_resource)
        ssh_manager.get_file(file_path, experiment_id)
    else:
        raise ValueError("{} - Please provide valid remote resource. {}".format(
                    experiment_id, remote_resource))

    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    # Goodbye message if successful
    print(time_t, "Successfully retrieved {} - from {}".format(file_path,
                                                               remote_resource))

    # Update protocol retrieval status of the experiment
    db.dadd(experiment_id, ("retrieved_results", True))
    db.dump()
