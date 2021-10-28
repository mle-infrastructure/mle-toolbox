from datetime import datetime
from mle_toolbox.utils import print_framed
from mle_toolbox.remote.ssh_manager import SSH_Manager
from mle_toolbox.remote.gcloud_transfer import get_gcloud_zip
from mle_toolbox.launch.prepare_experiment import ask_for_experiment_id
from mle_toolbox import mle_config
from mle_monitor import MLEProtocol


def retrieve(cmd_args):
    """Copy over experiment results folder from cluster."""
    experiment_id = cmd_args.experiment_id
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")

    protocol_db = MLEProtocol(
        mle_config.general.local_protocol_fname,
        mle_config.general.use_gcloud_protocol_sync,
        mle_config.gcp.project_name,
        mle_config.gcp.bucket_name,
        mle_config.gcp.protocol_fname,
        mle_config.general.local_protocol_fname,
        mle_config.gcp.credentials_path,
    )

    # Retrieve results for a single experiment
    if not cmd_args.retrieve_all_new:
        retrieval_counter = 0
        while True:
            # If no id given show last experiments & ask for input
            if experiment_id == "no-id-given" and retrieval_counter == 0:
                experiment_id = ask_for_experiment_id()
                if cmd_args.retrieve_local:
                    retrieve_single_experiment(protocol_db, experiment_id)
                else:
                    if cmd_args.local_dir_name is None:
                        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
                        local_dir_name = input(
                            time_t + " Local results directory name:  "
                        )
                    else:
                        local_dir_name = cmd_args.local_dir_name
                    get_gcloud_zip(protocol_db, experiment_id, local_dir_name)
                retrieval_counter += 1
            else:
                experiment_id, _, _ = ask_for_experiment_id(True)
                if experiment_id == "N":
                    break
                if cmd_args.retrieve_local:
                    retrieve_single_experiment(protocol_db, experiment_id)
                else:
                    if cmd_args.local_dir_name is None:
                        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
                        local_dir_name = input(
                            time_t + " Local results directory name:  "
                        )
                    else:
                        local_dir_name = cmd_args.local_dir_name
                    get_gcloud_zip(protocol_db, experiment_id, local_dir_name)
                retrieval_counter += 1
    else:
        list_of_new_e_ids = []
        for e_id in protocol_db.experiment_ids:
            completed = protocol_db.get(e_id, "job_status") == "completed"
            if completed and not protocol_db.get(e_id, "retrieve_results"):
                list_of_new_e_ids.append(e_id)

        for i, experiment_id in enumerate(list_of_new_e_ids):
            try:
                stored_in_gcloud = protocol_db.get(e_id, "stored_in_gcloud")
            except Exception:
                stored_in_gcloud = False
            # Pull either from remote machine or gcloud bucket
            if cmd_args.retrieve_local and not stored_in_gcloud:
                retrieve_single_experiment(protocol_db, experiment_id)
            else:
                if cmd_args.local_dir_name is None:
                    local_dir_name = input(time_t + " Local results directory name:  ")
                else:
                    local_dir_name = cmd_args.local_dir_name
                get_gcloud_zip(protocol_db, experiment_id, protocol_db.experiment_ids)
            print_framed(f"COMPLETED E-ID {i+1}/{len(list_of_new_e_ids)}")

    # (d) Send most recent/up-to-date experiment DB to GCS
    if mle_config.general.use_gcloud_protocol_sync:
        if protocol_db.accessed_gcs:
            protocol_db.gcs_send()
            time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
            print(
                time_t, "Updated retrieval protocol status & " "send to gcloud storage."
            )

    return local_dir_name


def retrieve_single_experiment(protocol_db: MLEProtocol, experiment_id: str):
    """Retrieve a single experiment from remote resource."""
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    # Get path to experiment results dir & get cluster to retrieve from
    file_path = protocol_db.get(experiment_id, "exp_retrieval_path")

    remote_resource = protocol_db.get(experiment_id, "exec_resource")
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print(
        time_t,
        "{} - Started retrieving {} - from {}".format(
            experiment_id, file_path, remote_resource
        ),
    )

    # Create SSH & SCP client - Pull files into new dir by name of exp-id
    if remote_resource in ["sge-cluster", "slurm-cluster"]:
        ssh_manager = SSH_Manager(remote_resource)
        ssh_manager.get_file(file_path, experiment_id)
    else:
        raise ValueError(
            "{} - Provide valid remote resource. {}".format(
                experiment_id, remote_resource
            )
        )

    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    # Goodbye message if successful
    print(time_t, f"Successfully retrieved {experiment_id} - from {remote_resource}")
    print(time_t, f"Remote Path: {file_path}")

    # Update protocol retrieval status of the experiment
    protocol_db.update(experiment_id, "retrieved_results", True)
