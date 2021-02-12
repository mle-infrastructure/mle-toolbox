import os
import re
import pickledb
import pandas as pd
from datetime import datetime
import sys, select
from tabulate import tabulate

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
    if len(all_experiment_ids) >0:
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
             "Seeds": num_seeds}
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


def update_protocol_status(experiment_id: str, job_status: str):
    """ Update the status of the experiment {running, completed, failed}. """
    # Load in the DB
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    # Update the job status of the experiment
    db.dadd(experiment_id, ("job_status", job_status))
    time_t = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    db.dadd(experiment_id, ("stop_time", time_t))
    db.dump()
    return db


def delete_protocol_from_input():
    """ Ask user if they want to delete previous experiment by id. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print("{} Want to delete experiment? - state its id: [e_id/N]".format(time_t), end=' ')
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
            print("{} The e_id is not in the protocol db. " \
                  "Please try again: [e_id/N]".format(time_t), end=' ')
        sys.stdout.flush()
