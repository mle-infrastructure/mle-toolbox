import os
import re
import pickledb
import pandas as pd
from datetime import datetime
import sys, select
from tabulate import tabulate
from typing import Union, List

from ..utils.general import load_mle_toolbox_config


def load_local_protocol_db():
    """ Load local database from config name & reconstruct experiment id. """
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
    if len(all_experiment_ids) > 0:
        all_experiment_ids.sort(key=natural_keys)
        last_experiment_id = int(all_experiment_ids[-1].split("-")[-1])
    else:
        last_experiment_id = 0
    return db, all_experiment_ids, last_experiment_id


def protocol_summary(tail: int=5, verbose: bool=True):
    """ Construct a summary dataframe of previous experiments. """
    # Load in the DB
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    # Set pandas df format option to print
    pd.set_option('display.max_columns', 5)
    pd.set_option('max_colwidth', 30)
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    if len(all_experiment_ids) > 0:
        purposes, project_names, exp_paths = [], [], []
        num_seeds, statuses, start_times, job_types = [], [], [], []
        resource, num_cpus, num_gpus, total_jobs = [], [], [], []
        if tail is None:
            tail = len(all_experiment_ids)
        for e_id in all_experiment_ids[-tail:]:
            purposes.append(db.dget(e_id, "purpose"))
            project_names.append(db.dget(e_id, "project_name"))
            exp_paths.append(db.dget(e_id, "exp_retrieval_path"))
            statuses.append(db.dget(e_id, "job_status"))
            start_times.append(db.dget(e_id, "start_time"))
            resource.append(db.dget(e_id, "exec_resource"))
            try:
                num_seeds.append(db.dget(e_id, "num_seeds"))
            except:
                num_seeds.append("-")
            job_args = db.dget(e_id, "single_job_args")
            num_cpus.append(job_args["num_logical_cores"])
            try:
                num_gpus.append(job_args["num_gpus"])
            except:
                num_gpus.append(0)

            # Get job type data
            meta_args = db.dget(e_id, "meta_job_args")
            if meta_args["job_type"] == "hyperparameter-search":
                job_types.append("search")
            elif meta_args["job_type"] == "multiple-experiments":
                job_types.append("multi")
            else:
                job_types.append("other")

            # Get number of jobs in experiement
            job_spec_args = db.dget(e_id, "job_spec_args")
            if meta_args["job_type"] == "hyperparameter-search":
                total_jobs.append(job_spec_args["num_search_batches"]
                                  * job_spec_args["num_iter_per_batch"]
                                  * job_spec_args["num_evals_per_iter"])
            elif meta_args["job_type"] == "multiple-experiments":
                total_jobs.append(len(job_spec_args["config_fnames"])*
                                  job_spec_args["num_seeds"])
            else:
                total_jobs.append(1)

        d = {"ID": all_experiment_ids[-tail:],
             "Date": start_times,
             "Project": project_names,
             "Purpose": purposes,
             "Experiment Dir": exp_paths,
             "Status": statuses,
             "Seeds": num_seeds,
             "Resource": resource,
             "CPUs": num_cpus,
             "GPUs": num_gpus,
             "Type": job_types,
             "Jobs": total_jobs}
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


def update_protocol_var(experiment_id: str,
                        db_var_name: Union[List[str], str],
                        db_var_value: Union[list, str, dict]):
    """ Update variable(s) stored in protocol db for an experiment. """
    # Load in the DB
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    # Update the variable(s) of the experiment
    if type(db_var_name) == list:
        for db_v_id in range(len(db_var_name)):
            db.dadd(experiment_id, (db_var_name[db_v_id],
                                    db_var_value[db_v_id]))
    else:
        db.dadd(experiment_id, (db_var_name, db_var_value))
    db.dump()
    return db


def delete_protocol_from_input():
    """ Ask user if they want to delete previous experiment by id. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    q_str = "{} Want to delete experiment? - state its id: [e_id/N]"
    print(q_str.format(time_t), end=' ')
    sys.stdout.flush()
    # Loop over experiments to delete until "N" given or timeout after 60 secs
    while True:
        i, o, e = select.select([sys.stdin], [], [], 60)
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
        db, all_experiment_ids, _ = load_local_protocol_db()
        # Delete the dictionary in DB corresponding to e-id
        try:
            db.drem(e_id)
            db.dump()
            print("{} Another one? - state the next id: [e_id/N]".format(
                time_t), end=' ')
        except:
            print("\n{} The e_id is not in the protocol db. " \
                  "Please try again: [e_id/N]".format(time_t), end=' ')
        sys.stdout.flush()


def abort_protocol_from_input():
    """ Ask user if they want to change experiment status to 'aborted'. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    q_str = "{} Want to set exp. status to aborted? - state its id: [e_id/N]"
    print(q_str.format(time_t), end=' ')
    sys.stdout.flush()
    # Loop over experiments to delete until "N" given or timeout after 60 secs
    while True:
        i, o, e = select.select([sys.stdin], [], [], 60)
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
        db, all_experiment_ids, _ = load_local_protocol_db()
        # Delete the dictionary in DB corresponding to e-id
        try:
            db.dadd(e_id, ("job_status", "aborted"))
            db.dump()
            print("{} Another one? - state the next id: [e_id/N]".format(
                time_t), end=' ')
        except:
            print("\n{} The e_id is not in the protocol db. " \
                  "Please try again: [e_id/N]".format(time_t), end=' ')
        sys.stdout.flush()
