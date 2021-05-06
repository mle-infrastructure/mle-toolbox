from dotmap import DotMap


general_descript = {'general':
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
                    'use_credential_encryption':
                        {'description': 'Whether to en/decrypt SSH credentials',
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
                }


slurm_descript = {'credentials':
          {'variables': {
                'user_name':
                    {'description': 'User name on Slurm cluster',
                     'type': str},
                'password':
                    {'description': 'Password on Slurm cluster',
                     'type': str},
                'aes_key':
                    {'description': 'AES key for SHA-256 crypto for Slurm',
                     'type': str},
                'gcp_credentials_path':
                    {'description': 'Path to GCP credentials',
                     'type': str}},
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
          'default_job_arguments':
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
         }


sge_descript = {'credentials':
          {'variables': {
                'user_name':
                    {'description': 'User name on SGE cluster',
                     'type': str},
                'password':
                    {'description': 'Password on SGE cluster',
                     'type': str},
                'aes_key':
                    {'description': 'AES key for SHA-256 crypto for SGE',
                     'type': str},
                'gcp_credentials_path':
                    {'description': 'Path to GCP credentials',
                     'type': str}},
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
         'default_job_arguments':
          {'variables': {
            'num_logical_cores':
                {'description': 'No. of cores for single job (0.5xthreads)',
                 'type': int},
            'queue':
                {'description': 'Queue to schedule job on',
                'type': str},
            'job_name':
                {'description': 'Job name extension (listed in qstat)',
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
         }


gcp_descript = {'gcp':
            {'variables': {
                'project_name':
                    {'description': 'Name of project in GCP account',
                     'type': str},
                'bucket_name':
                    {'description': 'Name of GCS bucket in GCP account',
                     'type': str},
                'protocol_fname':
                    {'description': 'Name of protocol db stored in bucket',
                     'type': str},
                'code_dir':
                    {'description': 'Name of GCS directory for local code',
                     'type': str},
                'results_dir':
                    {'description': 'Name of GCS directory for results',
                     'type': str},
             },
             'description': 'Settings specific to Google Cloud Platform'
            },
            'default_job_arguments':
             {'variables': {
               'num_logical_cores':
                   {'description': 'No. of cores for single job (0.5xthreads)',
                    'type': int},
                'num_gpus':
                    {'description': 'No. of attached GPUs',
                 'type': int},
                'use_tpus':
                    {'description': 'Whether to use a TPU VM',
                 'type': int},
               'job_name':
                   {'description': 'Job name extension (listed in gcloud)',
                    'type': str},
               'log_file':
                   {'description': 'Default log file base name',
                    'type': str},
               'err_file':
                   {'description': 'Default error file base name',
                    'type': str},
                   },
              'description': 'Default settings for a single job'
             }
}


# Dictionary with description and type of variables to modify
description_mle_config = DotMap({'general': general_descript,
                                 'slurm': slurm_descript,
                                 'sge': sge_descript,
                                 'gcp': gcp_descript})
