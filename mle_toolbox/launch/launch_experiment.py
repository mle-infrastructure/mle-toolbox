from .single_config import run_single_config
from .processing_job import run_processing_job
from .multi_config import run_multiple_configs
from .search_experiment import run_hyperparameter_search
from .prepare_experiment import prepare_logger
from ..utils import print_framed
from mle_toolbox import mle_config
from mle_monitor import MLEProtocol
from typing import Union


def launch_processing(
    preprocess: bool,
    resource_to_run: str,
    job_config: dict,
    no_protocol: bool = False,
    message_id: Union[str, None] = None,
    bot=None,
):
    if preprocess:
        print_framed("PRE-PROCESSING")
    else:
        print_framed("POST-PROCESSING")
    str_to_log = "Pre-processing" if preprocess else "Post-processing"
    logger = prepare_logger()
    logger.info(f"{str_to_log} job for experiment - STARTING")
    run_processing_job(
        resource_to_run,
        job_config.pre_processing_args,
        job_config.meta_job_args["experiment_dir"],
    )
    logger.info(f"{str_to_log} experiment results - COMPLETED")

    # Update slack bot experiment message - pre-processing
    if not no_protocol and mle_config.general.use_slack_bot:
        bot.reply(
            message_id,
            ":white_check_mark:" f" Finished {str_to_log}.",
            user_name=mle_config.slack.user_name,
        )


def launch_experiment(
    resource_to_run: str,
    job_config: dict,
    no_protocol: bool = False,
    message_id: Union[str, None] = None,
    protocol_db: Union[MLEProtocol, None] = None,
):
    print(mle_config.general.use_slack_bot)
    if not no_protocol and mle_config.general.use_slack_bot:
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
    else:
        bot = None
    # Perform pre-processing if arguments are provided
    if "pre_processing_args" in job_config.keys():
        launch_processing(True, job_config, no_protocol, message_id, bot)

    # Run the main experiment
    print_framed("RUN EXPERIMENT")
    # (a) Experiment: Run a single experiment
    if job_config.meta_job_args["experiment_type"] == "single-config":
        run_single_config(
            resource_to_run, job_config.meta_job_args, job_config.single_job_args
        )
    # (b) Experiment: Run training over different config files/seeds
    elif job_config.meta_job_args["experiment_type"] == "multiple-configs":
        if not no_protocol and mle_config.general.use_slack_bot:
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
        if not no_protocol and mle_config.general.use_slack_bot:
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

        if not no_protocol and mle_config.general.use_slack_bot:
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
    if not no_protocol and mle_config.general.use_slack_bot:
        bot.reply(
            message_id,
            ":steam_locomotive: "
            f"Finished main experiment: "
            f"`{job_config.meta_job_args['experiment_type']}`"
            " :steam_locomotive:",
            user_name=mle_config.slack.user_name,
        )

    # 10. Perform post-processing of results if arguments are provided
    if "post_processing_args" in job_config.keys():
        launch_processing(False, job_config, no_protocol, message_id, bot)