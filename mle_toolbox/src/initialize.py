import os
import sys
import select
import toml
import rich
from dotmap import DotMap
from datetime import datetime
from mle_toolbox.utils import load_mle_toolbox_config


def initialize():
    """ Setup toolbox .toml config with credentials/defaults. Structure:
        ├── general:
            +- development
            +- local_protocol_fname
            +- use_gcloud_protocol_sync
            +- use_gcloud_results_storage
            +- use_conda_virtual_env
            +- remote_env_name
        ├── slurm:
            +- credentials
                +- user_name
                +- password
            +- info
                +- head_names
                +- node_reg_exp
                +- partitions
                +- main_server_name
                +- jump_server_name
                +- ssh_port
                +- http_proxy
                +- https_proxy
            +- default_job_args
                +- num_logical_cores
                +- partition
                +- job_name
                +- log_file
                +- err_file
                +- env_name
        ├── sge:
            +- credentials
                +- user_name
                +- password
            +- info
                +- head_names
                +- node_reg_exp
                +- node_extension
                +- node_ids
                +- queue
                +- spare
                +- queue_base
                +- main_server_name
                +- jump_server_name
                +- ssh_port
                +- http_proxy
                +- https_proxy
            +- default_job_args
                +- num_logical_cores
                +- queue
                +- job_name
                +- log_file
                +- err_file
                +- env_name
        ├── gcp:
            +- slurm_gcloud_credentials_path
            +- sge_gcloud_credentials_path
            +- gcloud_project_name
            +- gcloud_bucket_name
            +- gcloud_protocol_fname
    """
    # Look for toml config and reload it exists - otherwise start w. default
    try:
        mle_config, reloaded_config = load_mle_toolbox_config(), True
    except:
        mle_config, reloaded_config = DotMap(default_toml_config), False

    # Pretty print current state of MLE-Toolbox configuration
    print_mle_config(mle_config)

    # Go through the base config and update entries - if user wants to
    base_keys = list(mle_config.keys())
    for k in base_keys:
        update = ask_whether_to_update(k)
        # Update value if user wants to do so
        if update and type(mle_config[k]) == DotMap:
            sub_keys = list(mle_config[k].keys())
            for sub_k in sub_keys:
                update_sub = ask_whether_to_update(sub_k)
                if update and type(mle_config[k][sub_k]) == DotMap:
                    ss_keys = list(mle_config[k][sub_k].keys())
                    for ss_k in ss_keys:
                        update_ss = ask_whether_to_update(ss_k)
                        if update_ss:
                            update_val = ask_how_to_update()
                        else:
                            pass
                elif update and type(mle_config[k][sub_k]) == str:
                    update_val = ask_how_to_update()
                else:
                    pass
        # Directly update value if shallow
        elif update and type(mle_config[k]) == str:
            update_val = ask_how_to_update()
        else:
            pass
    # Store the updated config file in ~/mle_config.toml
    return


def store_config_toml(toml_dict=os.path.expanduser("~/mle_config.toml")):
    """ Write the toml dictionary to a file. """
    with open(toml_fname, 'w') as f:
        new_toml_string = toml.dump(toml_dict, f)


def ask_whether_to_update(var_name):
    """ Ask if variable should be updated - if yes, move on to details. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print("{} Do you want to update {}: [Y/N]".format(time_t, var_name),
          end=' ')
    sys.stdout.flush()
    # Loop over experiments to delete until "N" given or timeout after 60 secs
    i, o, e = select.select([sys.stdin], [], [], 60)
    if (i):
        answer = sys.stdin.readline().strip()
    else:
        answer = "N"
    sys.stdout.flush()
    # TODO: Make more robust to input errors
    return (answer == "Y")


def ask_how_to_update():
    """ Ask how variable should be updated - get string/int. """
    print("ask for update")
    return


def update_toml_value(var, value):
    """ Ask if specific variable should be updated - if yes, do so. """
    with open(toml_fname, 'w') as f:
        new_toml_string = toml.dump(toml_dict, f)


def print_mle_config(mle_config):
    """ Print pretty version as rich table at init start and end. """
    # TODO: Implement pretty table layout.
    print(mle_config)


default_toml_config = {
    'title': 'mle-toolbox-config',
    'general': {'development': False,
                'local_protocol_fname': '~/local_robs_mle_protocol.db',
                'use_gcloud_protocol_sync': True,
                'use_gcloud_results_storage': True,
                'use_conda_virtual_env': True,
                'remote_env_name': 'mle-toolbox'},
    'slurm': {'credentials': {'user_name': '<slurm-user-name>',
                              'password': '<slurm-password>'},
              'info': {'head_names': ['<headnode1>'],
                       'node_reg_exp': ['<nodes-to-monitor1>'],
                       'partitions': ['<partition1>'],
                       'main_server_name': '<main-server-ip>',
                       'jump_server_name': '<jump-host-ip>',
                       'ssh_port': 22,
                       'http_proxy': 'http://<slurm_headnode>:3128/',
                       'https_proxy': 'http://<slurm_headnode>:3128/'},
              'default_job_args': {'num_logical_cores': 2,
                                   'partition': '<partition1>',
                                   'job_name': 'temp',
                                   'log_file': 'log',
                                   'err_file': 'err',
                                   'env_name': '<mle-default-env>'}},
    'sge': {'credentials': {'user_name': 'sge-user-name',
                            'password': 'sge-password'},
            'info': {'head_names': ['<headnode1>'],
                     'node_reg_exp': ['<nodes-to-monitor2>'],
                     'node_extension': '<ip-extension>',
                     'node_ids': ['00'],
                     'queue': '<sge-queue-name>',
                     'spare': '<sge-spare-name>',
                     'queue_base': '<sge-base-queue>',
                     'main_server_name': '<main-server-ip>',
                     'jump_server_name': '<jump-host-ip>',
                     'ssh_port': 22,
                     'http_proxy': 'http://<sge_headnode>:3128/',
                     'https_proxy': 'http://<sge_headnode>:3128/'},
            'default_job_arguments': {'num_logical_cores': 2,
                                      'queue': '<sge-queue-name>',
                                      'job_name': 'temp',
                                      'log_file': 'log',
                                      'err_file': 'err',
                                      'env_name': '<mle-default-env>'}},
    'gcp': {'slurm_gcloud_credentials_path': '~/<slurm_path_to_gc_cred>.json',
            'sge_gcloud_credentials_path': '~/<sge_path_to_gc_cred>.json',
            'gcloud_project_name': '<gcloud_project_name>',
            'gcloud_bucket_name': '<gcloud_bucket_name>',
            'gcloud_protocol_fname': 'gcloud_mle_protocol.db'}
    }
