from datetime import datetime
from mle_toolbox.utils import print_framed
from mle_toolbox import mle_config
from mle_toolbox.launch import prepare_logger
from mle_monitor import MLEProtocol
from mle_scheduler.ssh import SSH_Manager


def retrieve(cmd_args):
    """Copy over experiment results folder from cluster."""
    experiment_id = cmd_args.experiment_id
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    _ = prepare_logger()
    protocol_db = MLEProtocol(mle_config.general.local_protocol_fname, mle_config.gcp)

    # Retrieve results for a single experiment
    if not cmd_args.retrieve_all_new:
        retrieval_counter = 0
        while True:
            # If no id given show last experiments & ask for input
            if experiment_id == "no-id-given" and retrieval_counter == 0:
                protocol_db.summary(tail=10, verbose=True)
                experiment_id = protocol_db.ask_for_e_id("retrieve")
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
                    protocol_db.retrieve(experiment_id, local_dir_name)
                retrieval_counter += 1
            else:
                experiment_id = protocol_db.ask_for_e_id("retrieve")
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
                    protocol_db.retrieve(experiment_id, local_dir_name)
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
                protocol_db.retrieve(experiment_id, protocol_db.experiment_ids)
            print_framed(f"COMPLETED E-ID {i+1}/{len(list_of_new_e_ids)}")

    return local_dir_name


def retrieve_single_experiment(protocol_db: MLEProtocol, experiment_id: str):
    """Retrieve a single experiment from remote resource."""
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    # Get path to experiment results dir & get cluster to retrieve from
    file_path = protocol_db.get(experiment_id, "experiment_dir")

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
        # 0. Load the toolbox config, setup logger & ssh manager for local2remote
        if remote_resource == "slurm-cluster":
            resource = "slurm"
        elif remote_resource == "sge-cluster":
            resource = "sge"
        ssh_manager = SSH_Manager(
            user_name=mle_config[resource].credentials.user_name,
            pkey_path=mle_config.general.pkey_path,
            main_server=mle_config[resource].info.main_server_name,
            jump_server=mle_config[resource].info.jump_server_name,
            ssh_port=mle_config[resource].info.ssh_port,
        )

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
