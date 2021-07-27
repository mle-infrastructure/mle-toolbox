import os
import hashlib
import json
from datetime import datetime
import sys
import select
from typing import Union
from ..utils import load_json_config
from .protocol_helpers import load_local_protocol_db


def protocol_experiment(
    job_config: dict, resource_to_run: str, cmd_purpose: Union[None, str] = None
):
    """Protocol the new experiment."""
    # Load in the DB
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()

    # Create a new db experiment entry
    new_experiment_id = "e-id-" + str(last_experiment_id + 1)
    db.dcreate(new_experiment_id)

    # Add purpose of experiment - cmd args or timeout input after 30 secs
    if cmd_purpose is None:
        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        print(f"{time_t} Purpose of experiment?", end=" "),
        sys.stdout.flush()
        i, o, e = select.select([sys.stdin], [], [], 60)

        if i:
            purpose = sys.stdin.readline().strip()
        else:
            purpose = "default"
    else:
        purpose = " ".join(cmd_purpose)

    db.dadd(new_experiment_id, ("purpose", purpose))

    # Add the project name
    db.dadd(
        new_experiment_id, ("project_name", job_config.meta_job_args["project_name"])
    )

    # Add resource on which experiment was run
    db.dadd(new_experiment_id, ("exec_resource", resource_to_run))

    # Add the git latest commit hash
    try:
        import git

        g = git.Repo(search_parent_directories=True)
        git_hash = g.head.object.hexsha
    except Exception:
        git_hash = "no-git-repo"
    db.dadd(new_experiment_id, ("git_hash", git_hash))

    # Add remote URL to clone repository
    try:
        git_remote = g.remote(verbose=True).split("\t")[1].split(" (fetch)")[0]
    except Exception:
        git_remote = "no-git-remote"
    db.dadd(new_experiment_id, ("git_remote", git_remote))

    # Add the absolute path for retrieving the experiment
    exp_retrieval_path = os.path.join(
        os.getcwd(), job_config.meta_job_args["experiment_dir"]
    )
    db.dadd(new_experiment_id, ("exp_retrieval_path", exp_retrieval_path))

    # Add the meta experiment config
    db.dadd(new_experiment_id, ("meta_job_args", job_config.meta_job_args))
    db.dadd(new_experiment_id, ("single_job_args", job_config.single_job_args))

    if (
        db.dget(new_experiment_id, "meta_job_args")["experiment_type"]
        == "multiple-experiments"
    ):
        db.dadd(new_experiment_id, ("job_spec_args", job_config.multi_config_args))
    elif (
        db.dget(new_experiment_id, "meta_job_args")["experiment_type"]
        == "hyperparameter-search"
    ):
        db.dadd(new_experiment_id, ("job_spec_args", job_config.param_search_args))

    # Add the base config - train, model, log
    base_config = load_json_config(job_config.meta_job_args["base_train_config"])
    db.dadd(new_experiment_id, ("train_config", base_config["train_config"]))
    # Model/Network config is not required!
    try:
        db.dadd(new_experiment_id, ("model_config", base_config["model_config"]))
    except Exception:
        pass
    db.dadd(new_experiment_id, ("log_config", base_config["log_config"]))

    # Add the number of seeds over which experiment is run
    if job_config.meta_job_args["experiment_type"] == "hyperparameter-search":
        num_seeds = job_config.param_search_args.search_resources[
            "num_seeds_per_eval"
        ]  # noqa: disable=E501
    elif job_config.meta_job_args["experiment_type"] == "multiple-configs":
        num_seeds = job_config.multi_config_args["num_seeds"]
    else:
        num_seeds = 1
    db.dadd(new_experiment_id, ("num_seeds", num_seeds))

    # Gen unique experiment config hash - base_config + job_spec_args
    if job_config.meta_job_args["experiment_type"] == "hyperparameter-search":
        meta_to_hash = job_config.param_search_args
    elif job_config.meta_job_args["experiment_type"] == "multiple-configs":
        meta_to_hash = job_config.multi_config_args
    else:
        meta_to_hash = {}

    config_to_hash = dict(base_config)
    config_to_hash["meta_config"] = meta_to_hash
    config_to_hash = json.dumps(config_to_hash).encode("ASCII")

    hash_object = hashlib.md5(config_to_hash)
    experiment_hash = hash_object.hexdigest()
    db.dadd(new_experiment_id, ("e-hash", experiment_hash))

    # Set a boolean to indicate if results were previously retrieved
    db.dadd(new_experiment_id, ("retrieved_results", False))

    # Set a boolean to indicate if results were stored in GCloud Storage
    db.dadd(new_experiment_id, ("stored_in_gcloud", False))

    # Set a boolean to indicate if results were stored in GCloud Storage
    db.dadd(new_experiment_id, ("report_generated", False))

    # Set the job status to running
    db.dadd(new_experiment_id, ("job_status", "running"))
    time_t = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    db.dadd(new_experiment_id, ("start_time", time_t))

    # Save the newly updated DB to the file
    db.dump()
    return new_experiment_id
