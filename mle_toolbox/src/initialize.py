from dotmap import DotMap
from mle_toolbox.utils import load_mle_toolbox_config
from mle_toolbox.launch import prepare_logger
from mle_toolbox.initialize import (default_mle_config,
                                    description_mle_config,
                                    print_mle_config,
                                    whether_update_config,
                                    how_update_config,
                                    store_mle_config)


def initialize(cmd_args):
    """ Setup toolbox .toml config with credentials/defaults. Structure:
        ├── general: General settings unspecific to remote resource
            +- development: Whether to keep err/log files or to delete them
            +- local_protocol_fname: Where protocol db is locally stored
            +- use_gcloud_protocol_sync: Whether to sync protocol db with GCS
            +- use_gcloud_results_storage: Whether to sync exp results with GCS
            +- use_conda_virtual_env: Whether to use anaconda or venv
            +- remote_env_name: Env to activate at local launch of remote job
        ├── slurm: Settings specific to slurm clusters
            +- credentials: Credentials to submit jobs & retrieve results
            +- info: Info to setup network access, monitoring & local launch
            +- default_job_args: Default settings for a single job
        ├── sge: Settings specific to SunGridEngine clusters
            +- credentials: Credentials to submit jobs & retrieve results
            +- info: Info to setup network access, monitoring & local launch
            +- default_job_args: Default settings for a single job
        ├── gcp: Settings specific to Google Cloud Platform
            +- slurm_gcloud_credentials_path: Path to GCP credentials on Slurm
            +- sge_gcloud_credentials_path: Path to GCP credentials on SGE
            +- gcloud_project_name: Name of project in GCP account
            +- gcloud_bucket_name: Name of GCS bucket in GCP account
            +- gcloud_protocol_fname: Name of protocol db stored in bucket
    """
    # Look for toml config and reload it exists - otherwise start w. default
    try:
        mle_config, reloaded_config = load_mle_toolbox_config(), True
    except:
        mle_config, reloaded_config = default_mle_config, False

    # Pretty print current state of MLE-Toolbox configuration
    print_mle_config(mle_config)

    # Setup logger for configuration updates
    logger = prepare_logger()

    if not cmd_args.no_command_line:
        # Go through the base config and update entries - if user wants to
        # Loop over main categories in MLE config
        base_keys = list(description_mle_config.keys())
        logger.info(f'Main config categories: {base_keys}')
        for k in description_mle_config.keys():
            update = whether_update_config(k)
            # Update value if user wants to do so
            if update:
                # Loop over sub-categories in main
                sub_keys = list(description_mle_config[k].keys())
                logger.info(f'Sub-categories {k}: {sub_keys}')
                for sk in sub_keys:
                    ss_keys = list(description_mle_config[k][sk]["variables"].keys())
                    if k != sk:
                        update_sub = whether_update_config(sk)
                        # Loop over subsub-categories in sub
                        logger.info(f'Subsub-categories {sk}: {ss_keys}')
                        if update_sub:
                            for var in ss_keys:
                                update_ss = whether_update_config(var)
                                if update_ss:
                                    var_type = description_mle_config[k][sk]["variables"][var]["type"]
                                    update_val = how_update_config(var, var_type)
                                    mle_config[k][sk][var] = update_val
                                    logger.info(f'Updated {var}: {update_val}')
                                else:
                                    pass
                    else:
                        for var in ss_keys:
                            update_ss = whether_update_config(var)
                            if update_ss:
                                var_type = description_mle_config[k][sk]["variables"][var]["type"]
                                update_val = how_update_config(var, var_type)
                                mle_config[k][var] = update_val
                                logger.info(f'Updated {var}: {update_val}')
                else:
                    pass

    # Store the updated config file in ~/mle_config.toml
    store_mle_config(mle_config)

    # Pretty print stored state of MLE-Toolbox configuration
    # print_mle_config(mle_config)
    return
