import os
from datetime import datetime

from mle_toolbox.utils import print_framed
from mle_toolbox.remote.ssh_transfer import SSH_Manager
from mle_toolbox.remote.gcloud_transfer import (send_gcloud_db,
                                                get_gcloud_zip_experiment)
from mle_toolbox.launch.prepare_experiment import ask_for_experiment_id
from mle_toolbox.protocol import load_local_protocol_db


def retrieve(cmd_args):
    """ Copy over experiment results folder from cluster. """
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
                experiment_id, db, all_e_ids, accessed_remote_db = ask_for_experiment_id()
                if cmd_args.retrieve_local:
                    retrieve_single_experiment(db, experiment_id,
                                               get_dir_or_fig)
                else:
                    if cmd_args.local_dir_name is None:
                        local_dir_name = input(time_t +
                                         " Local results directory name:  ")
                    else:
                        local_dir_name = cmd_args.local_dir_name
                    get_gcloud_zip_experiment(db, experiment_id,
                                              all_e_ids,
                                              local_dir_name)
                retrieval_counter += 1
            else:
                experiment_id, _, _, _ = ask_for_experiment_id(True)
                if experiment_id == "N":
                    break
                if cmd_args.retrieve_local:
                    retrieve_single_experiment(db, experiment_id,
                                               get_dir_or_fig)
                else:
                    if cmd_args.local_dir_name is None:
                        local_dir_name = input(time_t +
                                         " Local results directory name:  ")
                    else:
                        local_dir_name = cmd_args.local_dir_name
                    get_gcloud_zip_experiment(db, experiment_id,
                                              all_e_ids,
                                              local_dir_name)
                retrieval_counter += 1
    else:
        list_of_new_e_ids = []
        db, all_e_ids, last_experiment_id = load_local_protocol_db()
        for e_id in all_e_ids:
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
                                           get_dir_or_fig)
            else:
                if cmd_args.local_dir_name is None:
                    local_dir_name = input(time_t +
                                           " Local results directory name:  ")
                else:
                    local_dir_name = cmd_args.local_dir_name
                get_gcloud_zip_experiment(db, experiment_id,
                                          all_e_ids)
            print_framed(f'COMPLETED E-ID {i+1}/{len(list_of_new_e_ids)}')

    if accessed_remote_db:
        send_gcloud_db()
        print(time_t, "Updated retrieval protocol status & "
              "send to gcloud storage.")


def retrieve_single_experiment(db, experiment_id: str,
                               get_dir_or_fig: str):
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
