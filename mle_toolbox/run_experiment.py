#!/usr/bin/env python
import os
import argparse
import numpy as np
from .utils import load_yaml_config, DotDic, determine_resource, print_framed
from .utils.file_transfer import (get_gcloud_db, send_gcloud_db,
                                  send_gcloud_zip_experiment)
from .utils.protocol_experiment import (protocol_new_experiment,
                                        protocol_summary,
                                        update_experiment_protocol_status,
                                        update_experiment_protocol_gcs_stored,
                                        delete_protocol_from_input)

from .src.prepare_experiment import (welcome_to_mle_toolbox,
                                     prepare_logger, check_job_config)
from .src import (run_single_experiment,
                  run_multiple_experiments,
                  run_hyperparameter_search,
                  run_post_processing)

import mle_toolbox.cluster_config as cc



def main():
    """ Main function of toolbox - Execute different types of experiments. """
    # -1. Greet the user with a fancy welcome ASCII
    welcome_to_mle_toolbox()

    # 0. Load in args for the Machine Learning Experiment + Determine resource
    def get_train_args():
        """ Get env name, config file path & device to train from cmd line """
        parser = argparse.ArgumentParser()
        parser.add_argument('config_fname', metavar='C', type=str,
                            default="experiment_config.yaml",
                            help ='Filename to load config yaml from')
        parser.add_argument('-d', '--debug', default=False, action='store_true',
                            help ='Run simulation in debug mode')
        parser.add_argument('-p', '--purpose', default=None, nargs='+',
                            help ='Purpose of the experiment to run')
        parser.add_argument('-np', '--no_protocol', default=False, action='store_true',
                            help ='Run simulation in without protocol recording')
        parser.add_argument('-del', '--delete_after_upload', default=False, action='store_true',
                            help ='Delete results after upload to GCloud.')
        return parser.parse_args()

    cmd_args = get_train_args()
    job_config = load_yaml_config(cmd_args.config_fname)
    resource = determine_resource()

    # 1. Set up logging config for experiment instance
    logger = prepare_logger(job_config.meta_job_args["experiment_dir"],
                            cmd_args.debug)
    logger.info(f"Loaded experiment config YAML: {cmd_args.config_fname}")
    logger.info(f"Run on resource: {resource}")

    # Add debug mode config to the meta argument dict
    if cmd_args.debug:
        job_config.meta_job_args["debug_mode"] = cmd_args.debug

    # 2. Check the job config to comply with the necessary ingredients
    check_job_config(job_config)

    # 3. Protocol if the experiment if desired (can also only be locally)!
    if not cmd_args.no_protocol:
        # 3a. Get most recent/up-to-date experiment DB from Google Cloud Storage
        if cc.use_gcloud_protocol_sync:
            accessed_remote_db = get_gcloud_db()
        else:
            accessed_remote_db = False

        # 3b. Meta-Protocol the experiment - Print last 5 exp. - Delete from input
        protocol_summary(tail=5, verbose=True)
        delete_protocol_from_input()
        new_experiment_id = protocol_new_experiment(job_config, cmd_args.purpose)
        logger.info(f'Updated protocol - STARTING: {new_experiment_id}')

        # 3c. Send most recent/up-to-date experiment DB to Google Cloud Storage
        if cc.use_gcloud_protocol_sync and accessed_remote_db:
            send_gcloud_db()

    # 4. Run an experiment
    print_framed("RUN EXPERIMENT")
    experiment_types = ["single-experiment",
                        "multiple-experiments",
                        "hyperparameter-search",
                        "population-based-training"]

    # (a) Experiment: Run a single experiment
    if job_config.meta_job_args["job_type"] == "single-experiment":
        run_single_experiment(DotDic(job_config.meta_job_args),
                              DotDic(job_config.single_job_args))

    # (b) Experiment: Run training over different config files/seeds
    elif job_config.meta_job_args["job_type"] == "multiple-experiments":
        run_multiple_experiments(DotDic(job_config.meta_job_args),
                                 DotDic(job_config.single_job_args),
                                 DotDic(job_config.multi_experiment_args))

    # (c) Experiment: Run hyperparameter search (Random, Grid, SMBO)
    elif job_config.meta_job_args["job_type"] == "hyperparameter-search":
        run_hyperparameter_search(DotDic(job_config.meta_job_args),
                                  DotDic(job_config.single_job_args),
                                  DotDic(job_config.param_search_args))

    # (d) Experiment: Run Population Based Training (Jaderberg et al., 2017)
    elif job_config.meta_job_args["job_type"] == "population-based-training":
        raise NotImplementedError
    else:
        raise ValueError(f'Please provide a valid experiment type: {experiment_types}.')
    logger.info(f'Finished running {job_config.meta_job_args["job_type"]} experiment')

    # 5. Perform post-processing of results if arguments are provided
    if job_config.post_process_args is not None:
        print_framed("POST-PROCESSING")
        logger.info(f"Post-processing experiment results - STARTING: {new_experiment_id}")
        run_post_processing(DotDic(job_config.post_process_args),
                            job_config.meta_job_args["experiment_dir"])
        logger.info(f"Post-processing experiment results - COMPLETED: {new_experiment_id}")

    # 6. Store experiment directory in GCS bucket under hash
    if (not cmd_args.no_protocol and cc.use_gcloud_results_storage
        and cc.use_gcloud_protocol_sync):
        send_gcloud_zip_experiment(job_config.meta_job_args["experiment_dir"],
                                   new_experiment_id,
                                   cmd_args.delete_after_upload)

    # 7. Update the experiment protocol & send back to GCS (if desired)
    if not cmd_args.no_protocol:
        # 7a. Get most recent/up-to-date experiment DB to Google Cloud Storage
        if cc.use_gcloud_protocol_sync and accessed_remote_db:
            get_gcloud_db()

        # 7b. Update the experiment protocol status
        logger.info(f'Updated protocol - COMPLETED: {new_experiment_id}')
        update_experiment_protocol_status(new_experiment_id, job_status="completed")

        # 7c. Send most recent/up-to-date experiment DB to Google Cloud Storage
        if cc.use_gcloud_protocol_sync and accessed_remote_db:
            send_gcloud_db()
    print(85*"=")


if __name__ == "__main__":
    main()
