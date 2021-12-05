import os
import shutil

# Import the MLE-Toolbox configuration
from mle_toolbox import mle_config

# Import of general tools (loading, etc.)
from mle_toolbox.utils import (
    load_experiment_config,
    determine_resource,
    print_framed,
    set_random_seeds,
    compose_protocol_data,
    setup_proxy_server,
)

# Import different experiment executers & setup tools (log, config, etc.)
from mle_toolbox.launch import (
    run_single_config,
    run_multiple_configs,
    run_processing_job,
    welcome_to_mle_toolbox,
    prepare_logger,
    check_experiment_config,
)

# Import of helpers for protocoling experiments
from mle_monitor import MLEProtocol


def run(cmd_args):
    """Main function of toolbox - Execute different types of experiments."""
    # Set environment variable for gcloud credentials & proxy remote
    setup_proxy_server()

    # 0. Set all random seeds for 'outer loop' toolbox experiment management
    set_random_seeds(mle_config.general.random_seed)

    # 1. Load in args for MLE + setup the experiment
    if not cmd_args.no_welcome:
        welcome_to_mle_toolbox()
    else:
        print_framed("EXPERIMENT START-UP")

    # Load experiment yaml config & determine exec resource
    job_config = load_experiment_config(cmd_args)
    current_resource = determine_resource()
    resource_to_run = cmd_args.resource_to_run
    job_config.meta_job_args.debug_mode = cmd_args.debug

    # 2. Set up logging config for experiment instance
    logger = prepare_logger()
    logger.info(f"Loaded configuration: {cmd_args.config_fname}")

    if resource_to_run is None:
        resource_to_run = current_resource
    logger.info(f"Run on resource: {resource_to_run}")

    # 4. Check experiment config to comply/include necessary ingredients
    job_config = check_experiment_config(job_config)

    # 5. Protocol experiment if desired (can also only be locally)!
    if not cmd_args.no_protocol:
        # Meta-protocol experiment - Print last ones - Delete from input
        protocol_db = MLEProtocol(
            mle_config.general.local_protocol_fname, mle_config.gcp
        )
        protocol_db.summary(tail=10, verbose=True)

        # Only ask to delete if no purpose given!
        if cmd_args.purpose is None:
            if len(protocol_db) > 0:
                protocol_db.ask_for_e_id(action="delete")
                protocol_db.ask_for_e_id(action="abort")
            purpose = protocol_db.ask_for_purpose()
        else:
            purpose = " ".join(cmd_args.purpose)

        meta_data, extra_data = compose_protocol_data(
            job_config, resource_to_run, purpose
        )
        new_experiment_id = protocol_db.add(meta_data, extra_data)
        logger.info(f"Updated protocol - STARTING: {new_experiment_id}")
    else:
        protocol_db = None

    # 6. Copy over the experiment config .yaml file for easy re-running
    os.makedirs(job_config.meta_job_args.experiment_dir, exist_ok=True)
    config_copy = os.path.join(
        job_config.meta_job_args.experiment_dir, "experiment_config.yaml"
    )
    if not os.path.exists(config_copy):
        shutil.copy(cmd_args.config_fname, config_copy)

    # 7. Setup cluster slack bot for status updates
    if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
        try:
            from clusterbot import ClusterBot, activate_logger

            activate_logger("WARNING")
        except ImportError:
            raise ImportError(
                "You need to install `slack-clusterbot` to " "use status notifications."
            )
        bot = ClusterBot(
            user_name=mle_config.slack.user_name,
            slack_token=mle_config.slack.slack_token,
        )
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
            protocol_db,
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
            protocol_db,
        )
    # (d) Experiment: Run population-based-training for NN training
    elif job_config.meta_job_args["experiment_type"] == "population-based-training":
        from ..experimental.pbt_experiment import run_population_based_training

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
                    new_experiment_id, protocol_db, logger, pdf_gen=True
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
        # (c) Update the experiment protocol status
        logger.info(f"Updated protocol - COMPLETED: {new_experiment_id}")
        protocol_db.complete(new_experiment_id, report_generated)

    print_framed("EXPERIMENT FINISHED")
    # Update slack bot experiment message - pre-processing
    if not cmd_args.no_protocol and mle_config.general.use_slack_bot:
        bot.reply(
            message_id,
            ":cloud: Finished protocol DB and GCS storage sync. :cloud:",
            user_name=mle_config.slack.user_name,
        )
