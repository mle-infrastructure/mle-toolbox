import os
import argparse
from datetime import datetime

from .utils import print_framed, load_mle_toolbox_config
from .protocol import protocol_summary, load_local_protocol_db
from .remote.ssh_transfer import get_file_scp, get_file_jump_scp
from .remote.gcloud_transfer import (get_gcloud_db, send_gcloud_db,
                                     get_gcloud_zip_experiment)


def main():
    """ Copy over experiment results folder from cluster. """
    # Load cluster config
    cc = load_mle_toolbox_config()
    # Get most recent/up-to-date experiment DB from Google Cloud Storage
    if cc.general.use_gcloud_protocol_sync:
        accessed_remote_db = get_gcloud_db()
    else:
        accessed_remote_db = False
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    if accessed_remote_db:
        print(time_t, "Successfully pulled latest experiment protocol from gcloud.")
    else:
        print(time_t, "Careful - you are using the local experiment protocol.")
    # Load in the experiment protocol DB
    db, all_experiment_ids, _ = load_local_protocol_db()

    # Get experiment id to retrieve from cmd
    def get_retrieve_args():
        """ Get env name, config file path & device to train from cmd line """
        parser = argparse.ArgumentParser()
        parser.add_argument('-e_id', '--experiment_id', type=str,
                            default="no-id-given",
                            help ='Filename to load config yaml from')
        parser.add_argument('-all_new', '--retrieve_all_new', default=False, action='store_true',
                            help ='Retrieve all new results.')
        parser.add_argument('-fig_dir', '--figures_dir', default=False, action='store_true',
                            help ='Retrieve only subdir containing figures.')
        parser.add_argument('-exp_dir', '--experiment_dir', default=False, action='store_true',
                            help ='Retrieve entire experiment dir.')
        parser.add_argument('-local', '--retrieve_local', default=False, action='store_true',
                            help ='Retrieve entire experiment dir from the remote directory.')
        return parser.parse_args()

    cmd_args = get_retrieve_args()
    experiment_id = cmd_args.experiment_id
    # Either get entire result dir or only generated figures - ask for input
    if cmd_args.figures_dir:
        get_dir_or_fig = "fig-dir"
    elif cmd_args.experiment_dir:
        get_dir_or_fig = "exp-dir"
    else:
        get_dir_or_fig = input(time_t + " Retrieve entire result dir or only figures? [exp-dir/fig-dir]  ")

    # Retrieve results for a single experiment
    if not cmd_args.retrieve_all_new:
        retrieval_counter = 0
        while True:
            # If no id given show last experiments & ask for input
            if experiment_id == "no-id-given" and retrieval_counter == 0:
                protocol_summary(tail=10)
                time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
                experiment_id = input(time_t + " Which experiment do you want to retrieve? [E-ID/N]:  ")
                if cmd_args.retrieve_local:
                    retrieve_single_experiment(db, experiment_id,
                                               get_dir_or_fig,
                                               all_experiment_ids)
                else:
                    get_gcloud_zip_experiment(db, experiment_id,
                                              all_experiment_ids)
                retrieval_counter += 1
            else:
                experiment_id = input(time_t + " Next experiment to retrieve [E-ID/N]:  ")
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
            if cmd_args.retrieve_local and not stored_in_gcloud:
                retrieve_single_experiment(db, experiment_id,
                                           get_dir_or_fig,
                                           all_experiment_ids)
            else:
                get_gcloud_zip_experiment(db, experiment_id,
                                          all_experiment_ids)
            print_framed(f'COMPLETED E-ID {i+1}/{len(list_of_new_e_ids)}')

    if cc.general.use_gcloud_protocol_sync and accessed_remote_db:
        send_gcloud_db()
        print(time_t, "Updated retrieval protocol status & send to gcloud storage.")


def retrieve_single_experiment(db, experiment_id: str,
                               get_dir_or_fig: str,
                               all_experiment_ids: list):
    # Ensure the right prefix
    while True:
        if experiment_id[:5] != "e-id-":
            experiment_id = "e-id-" + experiment_id

        if experiment_id not in all_experiment_ids:
            print(time_t, "The experiment you try to retrieve does not exist")
            experiment_id = input(time_t + " Which experiment do you want to retrieve?")
        else:
            break
    # Try to retrieve
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
            get_dir_or_fig = input(time_t + " Please repeat your input: [exp-dir/fig-dir]  ")

    remote_resource = db.dget(experiment_id, "exec_resource")
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print(time_t, "{} - Started retrieving {} - from {}".format(experiment_id,
                                                                file_path, remote_resource))

    # Create SSH & SCP client - Pull files into new dir by name of exp-id
    if remote_resource == "sge-cluster":
        get_file_scp(experiment_id, file_path, cc.sge.info.main_server_name,
                     cc.sge.credentials.user_name, cc.sge.credentialspassword,
                     cc.sge.info.ssh_port)
    elif remote_resource == "slurm-cluster":
        ssh = get_file_jump_scp(experiment_id, file_path,
                                cc.slurm.info.jump_server_name,
                                cc.slurm.info.main_server_name,
                                cc.slurm.info.user_name,
                                cc.slurm.info.password,
                                cc.sge.info.ssh_port)
    else:
        raise ValueError("{} - Please provide valid remote resource. {}".format(experiment_id,
                                                                                remote_resource))

    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    # Goodbye message if successful
    print(time_t, "Successfully retrieved {} - from {}".format(file_path,
                                                               remote_resource))

    # Update protocol retrieval status of the experiment
    db.dadd(experiment_id, ("retrieved_results", True))
    db.dump()
