import os
import sys
import select
import toml
from dotmap import DotMap
from datetime import datetime
from mle_toolbox.utils import load_mle_toolbox_config

from rich.console import Console
from rich.table import Table


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
                +- user_name: User name on Slurm cluster (TODO: make secure)
                +- password: Password on Slurm cluster (TODO: make secure)
            +- info: Info to setup network access, monitoring & local launch
                +- head_names: List of headnode names
                +- node_reg_exp: Regular expression of relevant nodes
                +- partitions: List of partitions to schedule on/monitor
                +- main_server_name: Main cluster server to log into via ssh
                +- jump_server_name: Jumphost to tunnel through
                +- ssh_port: SSH port exposed to network - access/send files
                +- http_proxy: Setup proxy server to tunnel through
                +- https_proxy: Setup proxy server to tunnel through
            +- default_job_args: Default settings for a single job
                +- num_logical_cores: No. of cores for single job (0.5xthreads)
                +- partition: Partition to schedule job on
                +- job_name: Job name extension (listed in qstat)
                +- log_file: Default log file base name
                +- err_file: Default error file base name
                +- env_name: Default environment to activate at job startup
        ├── sge: Settings specific to SunGridEngine clusters
            +- credentials: Credentials to submit jobs & retrieve results
                +- user_name: User name on SGE cluster (TODO: make secure)
                +- password: Password on SGE cluster (TODO: make secure)
            +- info: Info to setup network access, monitoring & local launch
                +- head_names: List of headnode names
                +- node_reg_exp: Regular expression of relevant nodes
                +- node_extension: IP extension to address cluster
                +- node_ids: List of numbers to add to regular expression
                +- queue: Grid engine queue to schedule on
                +- spare: (TODO: remove this)
                +- queue_base: ?
                +- main_server_name: Main cluster server to log into via ssh
                +- jump_server_name: Jumphost to tunnel through
                +- ssh_port: SSH port exposed to network - access/send files
                +- http_proxy: Setup proxy server to tunnel through
                +- https_proxy: Setup proxy server to tunnel through
            +- default_job_args: Default settings for a single job
                +- num_logical_cores: No. of cores for single job (0.5xthreads)
                +- queue: Queue to schedule job on
                +- job_name: Job name extension (listed in qstat)
                +- log_file: Default log file base name
                +- err_file: Default error file base name
                +- env_name: Default environment to activate at job startup
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
        mle_config, reloaded_config = DotMap(default_toml_config), False

    # Pretty print current state of MLE-Toolbox configuration
    print_mle_config(mle_config)

    # Go through the base config and update entries - if user wants to
    base_keys = list(mle_config.keys())
    print(base_keys)
    for k in base_keys:
        update = ask_whether_to_update(k)
        # Update value if user wants to do so
        if update and type(mle_config[k]) == DotMap:
            sub_keys = list(mle_config[k].keys())
            print(sub_keys)
            for sub_k in sub_keys:
                update_sub = ask_whether_to_update(sub_k)
                if update and type(mle_config[k][sub_k]) == DotMap:
                    ss_keys = list(mle_config[k][sub_k].keys())
                    print(ss_keys)
                    for ss_k in ss_keys:
                        update_ss = ask_whether_to_update(ss_k)
                        if update_ss:
                            update_val = ask_how_to_update()
                            mle_config[k][sub_k][ss_k] = update_val
                        else:
                            pass
                elif update and type(mle_config[k][sub_k]) in [str, int, bool]:
                    update_val = ask_how_to_update()
                    mle_config[k][sub_k] = update_val
                else:
                    pass

        # Directly update value if shallow
        elif update and type(mle_config[k]) == str:
            update_val = ask_how_to_update()
            mle_config[k] = update_val
        else:
            pass

    # Store the updated config file in ~/mle_config.toml
    store_config_toml(toml_dict=os.path.expanduser("~/mle_config_test.toml"))
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


def print_mle_config(mle_config):
    """ Print pretty version as rich table at init start and end. """
    # TODO: Implement pretty table layout.
    print(mle_config)
    console = Console()

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Date", style="dim", width=12)
    table.add_column("Title")
    table.add_column("Production Budget", justify="right")
    table.add_column("Box Office", justify="right")
    table.add_row(
        "Dev 20, 2019", "Star Wars: The Rise of Skywalker", "$275,000,000", "$375,126,118"
    )
    table.add_row(
        "May 25, 2018",
        "[red]Solo[/red]: A Star Wars Story",
        "$275,000,000",
        "$393,151,347",
    )
    table.add_row(
        "Dec 15, 2017",
        "Star Wars Ep. VIII: The Last Jedi",
        "$262,000,000",
        "[bold]$1,332,539,889[/bold]",
    )

    console.print(table)


default_toml_config = {
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


description_config = {
    'general': {'general':
                {'variables': {
                    'development':
                        {'description': 'Keep or delete err/log files',
                         'type': bool},
                    'local_protocol_fname':
                        {'description': 'Where protocol db is locally stored',
                         'type': str},
                    'use_gcloud_protocol_sync':
                        {'description': 'Whether to sync protocol db with GCS',
                         'type': bool},
                    'use_gcloud_results_storage':
                        {'description': 'Whether to sync exp results with GCS',
                         'type': bool},
                    'use_conda_virtual_env':
                        {'description': 'Whether to use anaconda or venv',
                         'type': bool},
                    'remote_env_name':
                        {'description': 'Activated env at local-remote launch',
                         'type': str}
                        },
                 'description': 'General settings unspecific to resource'
                 }
                },
    'slurm': {'credentials':
              {'variables': {
                    'user_name':
                        {'description': 'User name on Slurm cluster',
                         'type': str},
                    'password':
                        {'description': 'Password on Slurm cluster',
                         'type': str}
                        },
                'description': 'Slurm credentials to submit/retrieve jobs'
              },
              'info':
              {'variables': {
                    'head_names':
                        {'description': 'List of headnode names',
                         'type': list},
                    'node_reg_exp':
                        {'description': 'Regular expression of relevant nodes',
                         'type': list},
                    'partitions':
                        {'description': 'List of partitions - schedule/monitor',
                         'type': list},
                    'main_server_name':
                        {'description': 'Main cluster server to ssh into',
                         'type': str},
                    'jump_server_name':
                        {'description': 'Jumphost to tunnel through',
                         'type': str},
                    'ssh_port':
                        {'description': 'SSH port exposed to network',
                         'type': int},
                    'http_proxy':
                        {'description': 'Setup proxy server to tunnel through',
                         'type': str},
                    'https_proxy':
                        {'description': 'Setup proxy server to tunnel through',
                         'type': str}
                        },
                'description': 'Info to setup network, monitor & local launch'
              },
              'default_job_args':
              {'variables': {
                'num_logical_cores':
                    {'description': 'No. of cores for single job (0.5xthreads)',
                     'type': int},
                'partition':
                    {'description': 'Partition to schedule job on',
                    'type': str},
                'job_name':
                    {'description': 'Job name extension (listed in squeue)',
                     'type': str},
                'log_file':
                    {'description': 'Default log file base name',
                     'type': str},
                'err_file':
                    {'description': 'Default error file base name',
                     'type': str},
                'env_name':
                    {'description': 'Default env to activate at job startup',
                     'type': str},
                    },
               'description': 'Default settings for a single job'
              }
             },
    'sge': {'credentials':
              {'variables': {
                    'user_name':
                        {'description': 'User name on SGE cluster',
                         'type': str},
                    'password':
                        {'description': 'Password on SGE cluster',
                         'type': str}
                        },
                'description': 'SGE credentials to submit/retrieve jobs'
              },
             'info':
              {'variables': {
                    'head_names':
                        {'description': 'List of headnode names',
                         'type': list},
                    'node_reg_exp':
                        {'description': 'Regular expression of relevant nodes',
                         'type': list},
                    'node_extension':
                        {'description': 'IP extension to address cluster',
                         'type': str},
                    'node_ids':
                        {'description': 'List of # to extend reg. expression',
                         'type': list},
                    'queue':
                        {'description': 'Grid engine queue to schedule on',
                         'type': str},
                    'spare':
                        {'description': "?",
                         'type': str},
                    'queue_base':
                        {'description': "?",
                         'type': str},
                    'main_server_name':
                        {'description': 'Main cluster server to ssh into',
                         'type': str},
                    'jump_server_name':
                        {'description': 'Jumphost to tunnel through',
                         'type': str},
                    'ssh_port':
                        {'description': 'SSH port exposed to network',
                         'type': int},
                    'http_proxy':
                        {'description': 'Setup proxy server to tunnel through',
                         'type': str},
                    'https_proxy':
                        {'description': 'Setup proxy server to tunnel through',
                         'type': str}
                        },
                'description': 'Info to setup network, monitor & local launch'
              },
             'default_job_args':
              {'variables': {
                'num_logical_cores':
                    {'description': 'No. of cores for single job (0.5xthreads)',
                     'type': int},
                'queue':
                    {'description': 'Queue to schedule job on',
                    'type': str},
                'job_name':
                    {'description': 'Job name extension (listed in qstat)',
                     'type': },
                'log_file':
                    {'description': 'Default log file base name',
                     'type': str},
                'err_file':
                    {'description': 'Default error file base name',
                     'type': str},
                'env_name':
                    {'description': 'Default env to activate at job startup',
                     'type': str},
                    },
               'description': 'Default settings for a single job'
              }
             },
    'gcp': {'gcp':
                {'variables': {
                    'slurm_gcloud_credentials_path':
                        {'description': 'Path to GCP credentials on Slurm',
                         'type': str},
                    'sge_gcloud_credentials_path':
                        {'description': 'Path to GCP credentials on SGE',
                         'type': str},
                    'gcloud_project_name':
                        {'description': 'Name of project in GCP account',
                         'type': str},
                    'gcloud_bucket_name':
                        {'description': 'Name of GCS bucket in GCP account',
                         'type': str},
                    'gcloud_protocol_fname':
                        {'description': 'Name of protocol db stored in bucket',
                         'type': str},
                 'description': 'Settings specific to Google Cloud Platform'
                 }
                },
    }
