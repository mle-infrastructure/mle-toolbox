import os
import shutil
from datetime import datetime

# Import the MLE-Toolbox configuration
from mle_toolbox import mle_config

# Import of general tools (loading, etc.)
from mle_toolbox.utils import (
    load_yaml_config,
    determine_resource,
    ask_for_resource_to_run,
    ask_for_binary_input,
    print_framed,
    set_random_seeds,
)

# Import of helpers for protocoling experiments
from mle_toolbox.protocol import (
    protocol_summary,
    update_protocol_var,
    delete_protocol_from_input,
    abort_protocol_from_input,
    protocol_experiment,
)

# Import of local-to-remote helpers (verify, rsync, exec)
from mle_toolbox.remote.ssh_execute import (
    SSH_Manager,
    monitor_remote_session,
    run_remote_experiment,
)

# Import different experiment executers & setup tools (log, config, etc.)
from mle_toolbox.launch import (
    run_single_config,
    run_multiple_configs,
    run_processing_job,
    welcome_to_mle_toolbox,
    prepare_logger,
    check_job_config,
)


def run(cmd_args):
    """Main function of toolbox - Execute different types of experiments."""
    # 0. Set all random seeds for 'outer loop' toolbox experiment management
    set_random_seeds(mle_config.general.random_seed)

    # 1. Load in args for MLE + setup the experiment
    if not cmd_args.no_welcome:
        welcome_to_mle_toolbox()
    else:
        print_framed("EXPERIMENT STARTED")

    # Load experiment yaml config & determine exec resource
    job_config = load_yaml_config(cmd_args)
    current_resource = determine_resource()
    resource_to_run = cmd_args.resource_to_run
    job_config.meta_job_args.debug_mode = cmd_args.debug

    # 2. Set up logging config for experiment instance
    logger = prepare_logger()
    logger.info(f"Loaded experiment config YAML: {cmd_args.config_fname}")

    # 3. If local - check if experiment should be run on remote resource
    if current_resource not in ["sge-cluster", "slurm-cluster"] or (
        current_resource in ["sge-cluster", "slurm-cluster"]
        and resource_to_run is not None
    ):
        # Ask user on which resource to run on [local/sge/slurm/gcp]
        if cmd_args.resource_to_run is None:
            resource_to_run = ask_for_resource_to_run()

        # If locally launched & want to run on Slurm/SGE - execute on remote!
        if resource_to_run in ["slurm-cluster", "sge-cluster"]:
            if cmd_args.remote_reconnect:
                print_framed("RECONNECT TO REMOTE")
                ssh_manager = SSH_Manager(resource_to_run)
                base, fname_and_ext = os.path.split(cmd_args.config_fname)
                session_name, ext = os.path.splitext(fname_and_ext)
                monitor_remote_session(ssh_manager, session_name)
                return
            else:
                print_framed("TRANSFER TO REMOTE")
                if cmd_args.purpose is not None:
                    purpose = " ".join(cmd_args.purpose)
                else:
                    purpose = "Run on remote resource"
                run_remote_experiment(
                    resource_to_run,
                    cmd_args.config_fname,
                    job_config.meta_job_args.remote_exec_dir,
                    purpose,
                )
                # After successful completion on remote resource - BREAK
                return

    if resource_to_run is None:
        resource_to_run = current_resource
    logger.info(f"Run on resource: {resource_to_run}")

    # 4. Check experiment config to comply/include necessary ingredients
    check_job_config(job_config)

    # 5. Protocol experiment if desired (can also only be locally)!
    if not cmd_args.no_protocol:
        # 5a. Import gcloud protocol utilities if sync wanted
        if mle_config.general.use_gcloud_protocol_sync:
            try:
                # Import of helpers for GCloud storage of results/protocol
                from ..remote.gcloud_transfer import (
                    get_gcloud_db,
                    send_gcloud_db,
                    send_gcloud_zip_experiment,
                )
            except ImportError:
                raise ImportError(
                    "You need to install `google-cloud-storage` to "
                    "synchronize protocols with GCloud. Or set "
                    "`use_glcoud_protocol_sync = False` in your "
                    "config file."
                )

        # 5b. Get up-to-date experiment DB from Google Cloud Storage
        if mle_config.general.use_gcloud_protocol_sync:
            accessed_remote_db = get_gcloud_db()
        else:
            accessed_remote_db = False

        # 5c. Meta-protocol experiment - Print last ones - Delete from input
        protocol_df = protocol_summary(tail=10, verbose=True)

        # Only ask to delete if no purpose given!
        if cmd_args.purpose is None and protocol_df is not None:
            delete_protocol_from_input()
            abort_protocol_from_input()
        new_experiment_id, purpose = protocol_experiment(
            job_config, resource_to_run, cmd_args.purpose
        )
        logger.info(f"Updated protocol - STARTING: {new_experiment_id}")

        # 5d. Send recent/up-to-date experiment DB to Google Cloud Storage
        if mle_config.general.use_gcloud_protocol_sync and accessed_remote_db:
            send_gcloud_db()

    # 6. Copy over the experiment config .yaml file for easy re-running
    if not os.path.exists(job_config.meta_job_args.experiment_dir):
        try:
            os.makedirs(job_config.meta_job_args.experiment_dir)
        except Exception:
            pass
    config_copy = os.path.join(
        job_config.meta_job_args.experiment_dir, "experiment_config.yaml"
    )
    if not os.path.exists(config_copy):
        shutil.copy(cmd_args.config_fname, config_copy)

    # 7. Copy local code directory into GCP bucket if required
    if resource_to_run == "gcp-cloud":
        if "local_code_dir" in job_config.single_job_args.keys():
            local_code_dir = job_config.single_job_args["local_code_dir"]
        else:
            local_code_dir = os.getcwd()
        # Ask user if code dir should be uploaded + afterwards deleted
        copy_code_dir = ask_for_binary_input(
            "Do you want to copy local" + " directory to GCS bucket?"
        )
        delete_code_dir = ask_for_binary_input(
            "Do you want to delete GCS code" + " directory at completion?"
        )
        if copy_code_dir:
            logger.info(
                f"Start uploading {local_code_dir} to GCP bucket:"
                + f" {mle_config.gcp.code_dir}"
            )
            # Import utility to copy local code directory to GCS bucket
            from mle_toolbox.remote.gcloud_transfer import upload_local_dir_to_gcs

            upload_local_dir_to_gcs(
                local_path=local_code_dir, gcs_path=mle_config.gcp.code_dir
            )
            logger.info(
                f"Completed uploading {local_code_dir} to GCP "
                + f"bucket: {mle_config.gcp.code_dir}"
            )
        else:
            logger.info(
                f"Continue with {local_code_dir} previously stored "
                + f"in GCP bucket: {mle_config.gcp.code_dir}"
            )

    # Setup cluster slack bot for status updates
    if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
        try:
            from clusterbot import ClusterBot, activate_logger

            activate_logger("WARNING")
        except ImportError:
            raise ImportError(
                "You need to install `slack-clusterbot` to " "use status notifications."
            )
        bot = ClusterBot(user_name=mle_config.slack.user_name,
                         slack_token=mle_config.slack.slack_token)
        message_id = bot.send(
            f":rocket: Start experiment: `{new_experiment_id}` :rocket:\n"
            f"→ Config .yaml: `{cmd_args.config_fname}`\n"
            "→ Bash execution file:"
            f" `{job_config.meta_job_args.base_train_fname}`\n"
            "→ Base configuration file:"
            f" `{job_config.meta_job_args.base_train_config}`\n"
            f"→ Purpose: `{purpose}`\n"
            "→ Storage:"
            f" `{job_config.meta_job_args.experiment_dir}`\n"
            f"→ Compute resource: `{resource_to_run}`",
            user_name=mle_config.slack.user_name,
        )
    else:
        message_id = None

    # 8. Perform pre-processing if arguments are provided
    if "pre_processing_args" in job_config.keys():
        print_framed("PRE-PROCESSING")
        logger.info("Pre-processing job for experiment - STARTING")
        run_processing_job(
            resource_to_run,
            job_config.pre_processing_args,
            job_config.meta_job_args["experiment_dir"],
        )
        logger.info("Post-processing experiment results - COMPLETED")

        # Update slack bot experiment message - pre-processing
        if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
            bot.reply(
                message_id,
                ":white_check_mark:"
                f" Finished pre-processing for `{new_experiment_id}`",
                user_name=mle_config.slack.user_name,
            )

    # 9. Run the main experiment
    print_framed("RUN EXPERIMENT")
    # (a) Experiment: Run a single experiment
    if job_config.meta_job_args["experiment_type"] == "single-config":
        run_single_config(
            resource_to_run, job_config.meta_job_args, job_config.single_job_args
        )
    # (b) Experiment: Run training over different config files/seeds
    elif job_config.meta_job_args["experiment_type"] == "multiple-configs":
        if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
            message = "Multi-Config Resources & No. of Jobs:\n"
            for k, v in job_config.multi_config_args.items():
                message += f"→ {k}: `{v}` \n"
            bot.reply(message_id, message)

        run_multiple_configs(
            resource_to_run,
            job_config.meta_job_args,
            job_config.single_job_args,
            job_config.multi_config_args,
            message_id,
        )
    # (c) Experiment: Run hyperparameter search (Random, Grid, SMBO)
    elif job_config.meta_job_args["experiment_type"] == "hyperparameter-search":
        # Import only if needed due to optional dependency on scikit-optimize
        from ..launch import run_hyperparameter_search

        if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
            message = "Search Resources & No. of Jobs:\n"
            for k, v in job_config.param_search_args["search_resources"].items():
                message += f"→ {k}: `{v}` \n"
            bot.reply(message_id, message)

        run_hyperparameter_search(
            resource_to_run,
            job_config.meta_job_args,
            job_config.single_job_args,
            job_config.param_search_args,
            message_id,
        )
    # (d) Experiment: Run population-based-training for NN training
    elif job_config.meta_job_args["experiment_type"] == "population-based-training":
        from ..launch import run_population_based_training

        if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
            message = "PBT Resources & No. of Jobs:\n"
            for k, v in job_config.pbt_args["pbt_resources"].items():
                message += f"→ {k}: `{v}` \n"
            bot.reply(message_id, message)

        run_population_based_training(
            resource_to_run,
            job_config.meta_job_args,
            job_config.single_job_args,
            job_config.pbt_args,
        )

    # Update slack bot experiment message - main experiment jobs
    if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
        bot.reply(
            message_id,
            ":steam_locomotive: "
            f"Finished main experiment for `{new_experiment_id}`: "
            f"`{job_config.meta_job_args['experiment_type']}`"
            " :steam_locomotive:",
            user_name=mle_config.slack.user_name,
        )

    # 10. Perform post-processing of results if arguments are provided
    if "post_processing_args" in job_config.keys():
        print_framed("POST-PROCESSING")
        logger.info("Post-processing experiment results - STARTING")
        run_processing_job(
            resource_to_run,
            job_config.post_processing_args,
            job_config.meta_job_args["experiment_dir"],
        )
        logger.info("Post-processing experiment results - COMPLETED")

        # Update slack bot experiment message - pre-processing
        if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
            bot.reply(
                message_id,
                ":white_check_mark:"
                f" Finished post-processing for `{new_experiment_id}`"
                " :white_check_mark:",
                user_name=mle_config.slack.user_name,
            )

    # 11. Generate .md, and .html report w. figures for e_id - inherit logger
    report_generated = False
    if not cmd_args.no_protocol:
        if "report_generation" in job_config.meta_job_args.keys():
            if job_config.meta_job_args.report_generation:
                # Import for report generating after experiment finished
                from .report import auto_generate_reports

                reporter = auto_generate_reports(
                    new_experiment_id, logger, pdf_gen=True
                )
                report_generated = True
                print_framed("REPORT GENERATION FINISHED")

                if mle_config.general.use_slack_bot:
                    # Upload the report
                    bot.upload(
                        file_name=reporter.pdf_report_fname,
                        message=":scroll: Finished report generation :scroll:\n"
                        f" `{reporter.pdf_report_fname}`",
                        reply_to=message_id,
                        user_name=mle_config.slack.user_name,
                    )

    # 12. Update the experiment protocol & send back to GCS (if desired)
    if not cmd_args.no_protocol:
        # (a) Get most recent/up-to-date experiment DB to GCS
        if mle_config.general.use_gcloud_protocol_sync:
            get_gcloud_db()

        # (b) Store experiment directory in GCS bucket under hash
        if (
            mle_config.general.use_gcloud_results_storage
            and mle_config.general.use_gcloud_protocol_sync
        ):
            send_gcloud_zip_experiment(
                job_config.meta_job_args["experiment_dir"],
                new_experiment_id,
                cmd_args.delete_after_upload,
            )

        # (c) Update the experiment protocol status
        logger.info(f"Updated protocol - COMPLETED: {new_experiment_id}")
        time_t = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        update_protocol_var(
            new_experiment_id,
            db_var_name=["job_status", "stop_time", "report_generated"],
            db_var_value=["completed", time_t, report_generated],
        )

        # (d) Send most recent/up-to-date experiment DB to GCS
        if mle_config.general.use_gcloud_protocol_sync:
            send_gcloud_db()

    # 13. If job ran on GCP: Clean up & delete local code dir form GCS bucket
    if resource_to_run == "gcp-cloud":
        if delete_code_dir:
            # Import utility to delete directory in GCS bucket
            from mle_toolbox.remote.gcloud_transfer import delete_gcs_dir

            delete_gcs_dir(mle_config.gcp.code_dir)

    print_framed("EXPERIMENT FINISHED")
    # Update slack bot experiment message - pre-processing
    if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
        bot.reply(
            message_id,
            ":cloud: Finished protocol DB and GCS storage sync. :cloud:",
            user_name=mle_config.slack.user_name,
        )
