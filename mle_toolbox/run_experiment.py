#!/usr/bin/env python
import os
import numpy as np

# Import of general tools (loading, etc.)
from .utils import (load_mle_toolbox_config, load_yaml_config, DotDic,
                    determine_resource, print_framed)
# Import of helpers for GCloud storage of results/protocol
from .remote.gcloud_transfer import (get_gcloud_db, send_gcloud_db,
                                     send_gcloud_zip_experiment)
# Import of helpers for protocoling experiments
from .protocol import (protocol_summary, update_protocol_status,
                       delete_protocol_from_input)
from .protocol.protocol_experiment import protocol_new_experiment

# Import of setup tools for experiments (log, config, etc.)
from .src.prepare_experiment import (welcome_to_mle_toolbox, get_mle_args,
                                     prepare_logger, check_job_config)
# Import of local-to-remote helpers (verify, rsync, exec)
from .remote.ssh_execute import (ask_for_remote_resource,
                                 remote_connect_monitor_clean,
                                 run_remote_experiment)
# Import different experiment executers
from .src import (run_single_experiment,
                  run_multiple_experiments,
                  run_hyperparameter_search,
                  run_post_processing)


def main():
    """ Main function of toolbox - Execute different types of experiments. """
    # 1. Load in args for MLE + setup the experiment
    cmd_args = get_mle_args()
    if not cmd_args.no_welcome:
        welcome_to_mle_toolbox()

    job_config = load_yaml_config(cmd_args)
    cc = load_mle_toolbox_config()
    resource = determine_resource()
    if cmd_args.debug:
        job_config.meta_job_args["debug_mode"] = cmd_args.debug

    # 2. Set up logging config for experiment instance
    logger = prepare_logger(job_config.meta_job_args.experiment_dir,
                            job_config.meta_job_args.debug_mode)
    logger.info(f"Loaded experiment config YAML: {cmd_args.config_fname}")

    # 3. If local - check if experiment should be run on remote resource
    if resource not in ["sge-cluster", "slurm-cluster"]:
        # Ask user on which resource to run on
        if cmd_args.remote_resource is None:
            remote_resource = ask_for_remote_resource()
        else:
            remote_resource = cmd_args.remote_resource
        if remote_resource in ["slurm-cluster", "sge-cluster", "gcp-cloud"]:
            if cmd_args.remote_reconnect is not None:
                print_framed("RECONNECT TO REMOTE")
                remote_connect_monitor_clean(remote_resource,
                                             cmd_args.reconnect_remote)
                return
            else:
                print_framed("TRANSFER TO REMOTE")
                if cmd_args.purpose is not None:
                    purpose = " ".join(cmd_args.purpose)
                else:
                    purpose = "Run on remote resource"
                run_remote_experiment(remote_resource,
                                      cmd_args.config_fname,
                                      job_config.meta_job_args.remote_exec_dir,
                                      purpose)
                # After successful completion on remote resource - BREAK
                return
    logger.info(f"Run on resource: {resource}")

    # 4. Check the job config to comply with the necessary ingredients
    check_job_config(job_config)

    # 5. Protocol experiment if desired (can also only be locally)!
    if not cmd_args.no_protocol:
        # 3a. Get up-to-date experiment DB from Google Cloud Storage
        if cc.general.use_gcloud_protocol_sync:
            accessed_remote_db = get_gcloud_db()
        else:
            accessed_remote_db = False

        # 3b. Meta-protocol experiment - Print last ones - Delete from input
        protocol_summary(tail=10, verbose=True)

        # Only ask to delete if no purpose given!
        if cmd_args.purpose is None:
            delete_protocol_from_input()
        new_experiment_id = protocol_new_experiment(job_config,
                                                    cmd_args.purpose)
        logger.info(f'Updated protocol - STARTING: {new_experiment_id}')

        # 3c. Send most recent/up-to-date experiment DB to Google Cloud Storage
        if cc.general.use_gcloud_protocol_sync and accessed_remote_db:
            send_gcloud_db()

    # 6. Run an experiment
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

    # 7. Perform post-processing of results if arguments are provided
    if job_config.post_process_args is not None:
        print_framed("POST-PROCESSING")
        logger.info(f"Post-processing experiment results - STARTING: {new_experiment_id}")
        run_post_processing(DotDic(job_config.post_process_args),
                            job_config.meta_job_args["experiment_dir"])
        logger.info(f"Post-processing experiment results - COMPLETED: {new_experiment_id}")

    # 8. Store experiment directory in GCS bucket under hash
    if (not cmd_args.no_protocol and cc.general.use_gcloud_results_storage
        and cc.general.use_gcloud_protocol_sync):
        send_gcloud_zip_experiment(job_config.meta_job_args["experiment_dir"],
                                   new_experiment_id,
                                   cmd_args.delete_after_upload)

    # 9. Update the experiment protocol & send back to GCS (if desired)
    if not cmd_args.no_protocol:
        # 9a. Get most recent/up-to-date experiment DB to GCS
        if cc.general.use_gcloud_protocol_sync and accessed_remote_db:
            get_gcloud_db()

        # 9b. Update the experiment protocol status
        logger.info(f'Updated protocol - COMPLETED: {new_experiment_id}')
        update_protocol_status(new_experiment_id, job_status="completed")

        # 9c. Send most recent/up-to-date experiment DB to GCS
        if cc.general.use_gcloud_protocol_sync and accessed_remote_db:
            send_gcloud_db()
    print_framed("EXPERIMENT FINISHED")


if __name__ == "__main__":
    main()
