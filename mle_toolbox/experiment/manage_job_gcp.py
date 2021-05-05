import subprocess as sp
import time
from typing import Union
from .cloud.gcp.helpers_launch_gcp import (gcp_generate_startup_file,
                                           gcp_get_submission_cmd,
                                           gcp_delete_vm_instance)
from mle_toolbox import mle_config
from mle_toolbox.remote.gcloud_transfer import (upload_local_dir_to_gcs,
                                                delete_gcs_dir,
                                                download_gcs_dir)

# 1. How to also allow for bash script execution!? Not only python!
# 2. How to not copy over code to GCS for each experiment
# 3. Where to add experiment dir/all necessary ingredients os.getcwd() etc.
# 4. Make sure experiment results are archived nicely on local machine
# 5. Refactor everything into sub dirs: local, cluster, cloud


def gcp_check_job_args(job_arguments: Union[dict, None]) -> dict:
    """ Check the input job arguments & add default values if missing. """
    if job_arguments is None:
        job_arguments = {}

    # Add the default config values if they are missing from job_args
    for k, v in mle_config.gcp.default_job_arguments.items():
        if k not in job_arguments.keys():
            job_arguments[k] = v
    return DotMap(job_arguments)


def gcp_submit_job(filename: str,
                   config_filename: str,
                   cmd_line_arguments: str,
                   job_arguments: dict,
                   experiment_dir: str,
                   local_code_dir: str,
                   clean_up: bool=True):
    """ Create a GCP VM job & submit it based on provided file to execute. """
    # 0. Create VM Name - Timestamp + Random 4 digit id
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    random_str = str(random.randrange(1000, 9999))
    vm_name = '-'.join([job_args["job_name"], timestamp, random_str])
    vm_name = re.sub(r'[^a-z0-9-]', '-', vm_name)

    # 1. Copy local code directory into GCP bucket
    upload_local_dir_to_gcs(local_path=local_code_dir,
                            gcs_path=gcp_config.code_dir)

    # 2. Generate GCP startup file with provided arguments
    startup_fname = vm_name + "-startup.sh"
    gcp_generate_startup_file(gcp_config.code_dir, gcp_config.results_dir,
                              job_filename, config_filename,
                              experiment_dir, startup_fname,
                              gcp_config.bucket_name, job_args.use_tpus)

    # 3. Generate GCP submission command (`gcloud compute instance create ...`)
    gcp_launch_cmd, job_gcp_args = gcp_get_submission_cmd(
                                            vm_name, job_args,
                                            startup_fname
                                            )
    gcp_cmd_str = " ".join(gcp_launch_cmd)

    # 4. Launch GCP VM Instance - Everything handled by startup file
    sp.run(vm_instance_cmd)

    # 5. Wait until job is listed as running (ca. 2 minute!)
    for i in range(50):
        try:
            job_running = gcp_monitor_remote_job(vm_name, use_tpu)
            if job_running:
                # Delete statup bash file
                try:
                    os.remove(startup_fname)
                    gcp_logger.log(f"Deleted Startup File: {startup_fname}")
                except:
                    pass
                return vm_name
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            time.sleep(2)

    # Return -1 if job was not listed as starting/running within 100 seconds!
    return -1


def gcp_monitor_job(vm_name: str, job_arguments: dict):
    """ Monitor status of job based on vm_name. Requires stable connection. """
    # Check VM status from command line
    use_tpu = job_arguments.use_tpus
    while True:
        try:
            check_cmd = (["gcloud", "alpha", "compute", "tpus", "--zone",
                          "europe-west4-a", "--no-user-output-enabled",
                          "--verbosity", "error"]
                         if use_tpu else ["gcloud", "compute", "instances",
                                          "list", "--no-user-output-enabled",
                                          "--verbosity", "error"])
            out = sp.check_output(check_cmd)
            break
        except sp.CalledProcessError as e:
            stderr = e.stderr
            return_code = e.returncode
            time.sleep(1)

    # Clean up and check if vm_name is in list of all jobs
    job_info = out.split(b'\n')[1:-1]
    running_job_names = []
    for i in range(len(job_info)):
        decoded_job_info = job_info[i].decode("utf-8").split()
        if decoded_job_info[-1] in ["STAGING", "RUNNING"]:
            running_job_names.append(decoded_job_info[0])
    job_status = (vm_name in running_job_names)
    return job_status


def gcp_clean_up(vm_name: str, job_arguments: dict):
    """ Delete VM instance and code GCS directory. """
    # Delete GCP Job after it terminated (avoid storage billing)
    gcp_delete_vm_instance(vm_name, job_arguments.ZONE, job_arguments.use_tpus)

    # Delete code dir in GCS bucket (only keep results of computation)
    delete_gcs_dir(gcs_path=gcp_config.code_dir,
                   gcp_project_name=mle_config.gcp.project_name,
                   gcp_bucket_name=mle_config.gcp.bucket_name)

    # TODO: Download results back to local directory
    download_gcs_dir(gcs_path=os.path.join(self.gcp_config.results_dir,
                                           self.experiment_dir),
                     local_path=".",
                     gcp_project_name=self.gcp_config.project_name,
                     gcp_bucket_name=self.gcp_config.bucket_name)
