from mle_toolbox.utils import load_mle_toolbox_config
from mle_toolbox.initialize import (default_mle_config,
                                    print_mle_config,
                                    whether_update_config,
                                    how_update_config,
                                    store_mle_config)


def initialize():
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

    # Go through the base config and update entries - if user wants to
    base_keys = list(mle_config.keys())
    print(base_keys)
    for k in base_keys:
        update = whether_update_config(k)
        # Update value if user wants to do so
        if update and type(mle_config[k]) == DotMap:
            sub_keys = list(mle_config[k].keys())
            print(sub_keys)
            for sub_k in sub_keys:
                update_sub = whether_update_config(sub_k)
                if update and type(mle_config[k][sub_k]) == DotMap:
                    ss_keys = list(mle_config[k][sub_k].keys())
                    print(ss_keys)
                    for ss_k in ss_keys:
                        update_ss = whether_update_config(ss_k)
                        if update_ss:
                            update_val = how_update_config(k)
                            mle_config[k][sub_k][ss_k] = update_val
                        else:
                            pass
                elif update and type(mle_config[k][sub_k]) in [str, int, bool]:
                    update_val = how_update_config(k)
                    mle_config[k][sub_k] = update_val
                else:
                    pass

        # Directly update value if shallow
        elif update and type(mle_config[k]) == str:
            update_val = how_update_config(k)
            mle_config[k] = update_val
        else:
            pass

    # Store the updated config file in ~/mle_config.toml
    import os
    store_mle_config(mle_config, os.path.expanduser("~/mle_config_test.toml"))

    # Pretty print stored state of MLE-Toolbox configuration
    print_mle_config(mle_config)
    return
