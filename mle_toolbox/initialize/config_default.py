from dotmap import DotMap

# Default toml dictionary - copy and modify if there is no previous config

general_default = {'development': False,
                   'local_protocol_fname': '~/local_robs_mle_protocol.db',
                   'use_gcloud_protocol_sync': True,
                   'use_gcloud_results_storage': True,
                   'use_credential_encryption': True,
                   'use_conda_virtual_env': True,
                   'remote_env_name': 'mle-toolbox'}


slurm_default = {'credentials': {'user_name': '<slurm-user-name>',
                                 'password': '<slurm-password>',
                                 'aes_key': '<aes_crypto_key>',
                                 'gcp_credentials_path': '~/<path_to_gcp_cred>.json',},
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
                                      'env_name': '<mle-default-env>'}}


sge_default = {'credentials': {'user_name': 'sge-user-name',
                               'password': 'sge-password',
                               'aes_key': '<aes_crypto_key>',
                               'gcp_credentials_path': '~/<path_to_gcp_cred>.json',},
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
                                          'env_name': '<mle-default-env>'}}


gcp_default = {'project_name': '<gcloud_project_name>',
               'bucket_name': '<gcloud_bucket_name>',
               'protocol_fname': 'gcloud_mle_protocol.db',
               'code_dir': 'mle_experiments_code',
               'results_dir': 'mle_experiments_results',
               'default_job_arguments': {'num_logical_cores': 2,
                                         'num_gpus': 0,
                                         'use_tpus': False,
                                         'log_file': 'log',
                                         'err_file': 'err'}}


default_mle_config = DotMap({'general': general_default,
                             'slurm': slurm_default,
                             'sge': sge_default,
                             'gcp': gcp_default})
