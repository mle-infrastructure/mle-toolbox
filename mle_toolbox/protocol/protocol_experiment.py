import os
import re
import hashlib
import json
import argparse
import pickledb
import pandas as pd
from datetime import datetime
import sys, select
from typing import Union
from tabulate import tabulate

from ..utils.general import (load_config, determine_resource,
                             load_mle_toolbox_config)


def load_experiment_db():
    """ Load database from config name & reconstruct experiment id. """
    cc = load_mle_toolbox_config()
    db = pickledb.load(cc.general.local_protocol_fname, False)
    # Get the most recent experiment id
    all_experiment_ids = list(db.getall())

    def natural_keys(text: str):
        """ Helper function for sorting alpha-numeric strings. """
        def atoi(text):
            return int(text) if text.isdigit() else text
        return [atoi(c) for c in re.split(r'(\d+)', text)]

    # Sort experiment ids & get the last one
    if len(all_experiment_ids) >0:
        all_experiment_ids.sort(key=natural_keys)
        last_experiment_id = int(all_experiment_ids[-1].split("-")[-1])
    else:
        last_experiment_id = 0
    return db, all_experiment_ids, last_experiment_id


def protocol_new_experiment(job_config: dict,
                            cmd_purpose: Union[None, str]=None):
    """ Protocol the new experiment. """
    # Load in the DB
    db, all_experiment_ids, last_experiment_id = load_experiment_db()

    # Create a new db experiment entry
    new_experiment_id = "e-id-" + str(last_experiment_id + 1)
    db.dcreate(new_experiment_id)

    # Add purpose of experiment - cmd args or timeout input after 30 secs
    if cmd_purpose is None:
        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        print("{} Purpose of experiment?".format(time_t), end= ' '),
        sys.stdout.flush()
        i, o, e = select.select([sys.stdin], [], [], 20)

        if (i):
            purpose = sys.stdin.readline().strip()
        else:
            purpose = "default"
    else:
        purpose = ' '.join(cmd_purpose)

    db.dadd(new_experiment_id, ("purpose", purpose))

    # Add the project name
    db.dadd(new_experiment_id, ("project_name",
                                job_config.meta_job_args["project_name"]))

    # Add resource on which experiment was run
    resource = determine_resource()
    db.dadd(new_experiment_id, ("exec_resource", resource))

    # Add the git latest commit hash
    try:
        import git
        repo = git.Repo(search_parent_directories=True)
        git_hash = repo.head.object.hexsha
    except:
        git_hash = "no-git-repo"
    db.dadd(new_experiment_id, ("git_hash", git_hash))

    # Add remote URL to clone repository
    try:
        git_remote = g.remote(verbose=True).split("\t")[1].split(" (fetch)")[0]
    except:
        git_remote = "no-git-remote"
    db.dadd(new_experiment_id, ("git_remote", git_remote))

    # Add the absolute path for retrieving the experiment
    exp_retrieval_path = os.path.join(os.getcwd(),
                                      job_config.meta_job_args["experiment_dir"])
    db.dadd(new_experiment_id, ("exp_retrieval_path", exp_retrieval_path))

    # Add the meta experiment config
    db.dadd(new_experiment_id, ("meta_job_args", job_config.meta_job_args))
    db.dadd(new_experiment_id, ("single_job_args", job_config.single_job_args))

    if db.dget(new_experiment_id, "meta_job_args")["job_type"] == "multiple-experiments":
        db.dadd(new_experiment_id, ("job_spec_args", job_config.multi_experiment_args))
    elif db.dget(new_experiment_id, "meta_job_args")["job_type"] == "hyperparameter-search":
        db.dadd(new_experiment_id, ("job_spec_args", job_config.param_search_args))

    # Add the base config - train, net, log
    base_config = load_config(job_config.meta_job_args["base_train_config"])
    db.dadd(new_experiment_id, ("train_config", base_config["train_config"]))
    db.dadd(new_experiment_id, ("net_config", base_config["net_config"]))
    db.dadd(new_experiment_id, ("log_config", base_config["log_config"]))

    # Add the number of seeds over which experiment is run
    if job_config.meta_job_args["job_type"] == "hyperparameter-search":
        num_seeds = job_config.param_search_args["num_evals_per_iter"]
    elif job_config.meta_job_args["job_type"] == "multiple-experiments":
        num_seeds = job_config.multi_experiment_args["num_seeds"]
    else:
        num_seeds = 1
    db.dadd(new_experiment_id, ("num_seeds", num_seeds))

    # Gen unique experiment config hash - base_config + job_spec_args
    if job_config.meta_job_args["job_type"] == "hyperparameter-search":
        meta_to_hash = job_config.param_search_args
    elif job_config.meta_job_args["job_type"] == "multiple-experiments":
        meta_to_hash = job_config.multi_experiment_args
    else:
        meta_to_hash = {}

    config_to_hash = dict(base_config)
    config_to_hash["meta_config"] = meta_to_hash
    config_to_hash = json.dumps(config_to_hash).encode('ASCII')

    hash_object = hashlib.md5(config_to_hash)
    experiment_hash = hash_object.hexdigest()
    db.dadd(new_experiment_id, ("e-hash", experiment_hash))

    # Add path to generated figures if postprocessing is done in the end
    if job_config.post_process_args is not None:
        figure_path = job_config.post_process_args["extra_cmd_line_input"]["figures_dir"]
        db.dadd(new_experiment_id, ("figures_dir", figure_path))

    # Set a boolean to indicate if results were previously retrieved
    db.dadd(new_experiment_id, ("retrieved_results", False))

    # Set a boolean to indicate if results were stored in GCloud Storage
    db.dadd(new_experiment_id, ("stored_in_gcloud", False))

    # Set the job status to running
    db.dadd(new_experiment_id, ("job_status", "running"))
    time_t = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    db.dadd(new_experiment_id, ("start_time", time_t))

    # Save the newly updated DB to the file
    db.dump()
    return new_experiment_id


def update_protocol_status(experiment_id: str, job_status: str):
    """ Update the status of the experiment {running, completed, failed}. """
    # Load in the DB
    db, all_experiment_ids, last_experiment_id = load_experiment_db()
    # Update the job status of the experiment
    db.dadd(experiment_id, ("job_status", job_status))
    time_t = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    db.dadd(experiment_id, ("stop_time", time_t))
    db.dump()
    return db


def protocol_summary(tail: int=5, verbose: bool=True):
    """ Construct a summary dataframe of previous experiments. """
    # Load in the DB
    db, all_experiment_ids, last_experiment_id = load_experiment_db()
    # Set pandas df format option to print
    pd.set_option('display.max_columns', 5)
    pd.set_option('max_colwidth', 30)
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    if len(all_experiment_ids) > 0:
        purposes, project_names, exp_paths = [], [], []
        num_seeds, statuses, start_times = [], [], []
        if tail is None:
            tail = len(all_experiment_ids)
        for e_id in all_experiment_ids[-tail:]:
            purposes.append(db.dget(e_id, "purpose"))
            project_names.append(db.dget(e_id, "project_name"))
            exp_paths.append(db.dget(e_id, "exp_retrieval_path"))
            statuses.append(db.dget(e_id, "job_status"))
            start_times.append(db.dget(e_id, "start_time"))
            try:
                num_seeds.append(db.dget(e_id, "num_seeds"))
            except:
                num_seeds.append("-")

        d = {"ID": all_experiment_ids[-tail:],
             "Date": start_times,
             "Project": project_names,
             "Purpose": purposes,
             "Experiment Dir": exp_paths,
             "Status": statuses,
             "Seeds": num_seeds
             }
        df = pd.DataFrame(d)
        df["ID"] = [e.split("-")[-1] for e in df["ID"]]
        df["Date"] = df["Date"].map('{:.5}'.format)
        df["Purpose"] = df["Purpose"].map('{:.30}'.format)
        if verbose:
            print(time_t, "These were your most recent experiments:")
            print(tabulate(df[["ID", "Date", "Project", "Purpose", "Status", "Seeds"]],
                           headers='keys', tablefmt='psql', showindex=False))
        return df
    else:
        if verbose:
            print(time_t, "No previously recorded experiments")
        return None


def delete_protocol_from_input():
    """ Ask user if they want to delete previous experiment by id. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print("{} Want to delete an experiment? - state its id: [e_id/N]".format(time_t), end=' ')
    sys.stdout.flush()
    # Loop over experiments to delete until "N" given as input or timeout
    while True:
        i, o, e = select.select([sys.stdin], [], [], 15)
        if (i):
            e_id = sys.stdin.readline().strip()
            if e_id == "N":
                break
        else:
            break

        # Make sure e_id can access db via key
        if e_id[:5] != "e-id-":
            e_id = "e-id-" + e_id

        # Load in the experiment protocol DB
        db, all_experiment_ids, _ = load_experiment_db()
        # Delete the dictionary in DB corresponding to e-id
        db.drem(e_id)
        db.dump()
        print("{} Another one? - state the next id: [e_id/N]".format(time_t), end=' ')
        sys.stdout.flush()
