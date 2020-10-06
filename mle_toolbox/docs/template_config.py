# MLE-Toolbox Configuration File - Credentials & Cluster Info
# Modify this file depending on your cluster configuration

#------------------------------------------------------------------------------#
# 1. General Toolbox Configuration - Verbosity + Whether to use GCS Storage
#------------------------------------------------------------------------------#
# Store a full log of every experiment run in .txt file
development = True

# Set boolean for syncing protocol with GCloud & Storing all results in bucket 
use_gcloud_protocol_sync = False
use_gcloud_results_storage = False

#------------------------------------------------------------------------------#
# 2. Configuration for Slurm Cluster
#------------------------------------------------------------------------------#
# Slurm credentials - Needed only if you want to retrieve results from cluster
slurm_user_name = '<slurm-user-name>'
slurm_password = '<slurm-password>'

# Cluster-specific headnode name & partitions to monitor & use
slurm_head_names = ['<headnode1>']
slurm_node_reg_exp = ['<nodes-to-monitor1>']
slurm_partitions = ['<partition1>']

# Cluster-specific info for results retrieval & internet tunneling
slurm_main_server_name = '<main-server-ip>'
slurm_jump_server_name = '<jump-host-ip>'
slurm_http_proxy = "http://<slurm_headnode>:3128/"
slurm_https_proxy = "http://<slurm_headnode>:3128/"

# Default Slurm job arguments (if not supplied in job .yaml config)
slurm_default_job_arguments = {'num_logical_cores': 2,
                               'partition': '<partition1>',
                               'job_name': 'temp',
                               'log_file': 'log',
                               'err_file': 'err',
                               'env_name': '<mle-default-env>'}

#------------------------------------------------------------------------------#
# 3. Configuration for SunGridEngine Cluster
#------------------------------------------------------------------------------#
# SGE credentials - Needed only if you want to retrieve results from cluster
sge_user_name = 'sge-user-name'
sge_password = 'sge-password'

# Cluster-specific headnode name & queues to monitor & use
sge_head_names = ['<headnode1>']
sge_node_reg_exp = ['<nodes-to-monitor2>']
sge_node_extension = '<ip-extension>'
sge_node_ids = ['00']
sge_queue = '<sge-queue-name>'
sge_spare = '<sge-spare-name>'

# Cluster-specific info for results retrieval & internet tunneling
sge_queue_base = '<sge-base-queue>'
sge_server_name = 'main-server-ip'
sge_http_proxy = "http://<sge_headnode>:3128/"
sge_https_proxy = "http://<sge_headnode>:3128/"

# Default SGE job arguments (if not differently supplied)
sge_default_job_arguments = {'num_logical_cores': 2,
                             'queue': '<sge-queue-name>',
                             'job_name': 'temp',
                             'log_file': 'log',
                             'err_file': 'err',
                             'env_name': 'mle-default-env'}


#------------------------------------------------------------------------------#
# 4. GCP Config - Credentials, Project + Buffer for Meta-Experiment Protocol
#------------------------------------------------------------------------------#
# Set absolute path to the GCloud .json credentials - on Slurm/SGE cluster
slurm_gcloud_credentials_path = "~/<slurm_path_to_gcloud_credentials>.json"
sge_gcloud_credentials_path = "~/<sge_path_to_gcloud_credentials>.json"

# Set GCloud project and bucket name for storage/compute instances
gcloud_project_name = "<gcloud_project_name>"
gcloud_bucket_name = "<gcloud_bucket_name>"

# Filename to retrieve from gcloud bucket & where to store
gcloud_protocol_fname = "gcloud_mle_protocol.db"
local_protocol_fname = "~/local_mle_protocol.db"

