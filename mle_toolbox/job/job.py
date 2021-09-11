import os
import glob
import time
import logging
from typing import Union
from .manage_job_local import (
    local_check_job_args,
    local_submit_job,
    local_submit_venv_job,
    local_submit_conda_job,
)
from .manage_job_sge import sge_check_job_args, sge_submit_job, sge_monitor_job
from .manage_job_slurm import slurm_check_job_args, slurm_submit_job, slurm_monitor_job
from .manage_job_gcp import (
    gcp_check_job_args,
    gcp_submit_job,
    gcp_monitor_job,
    gcp_clean_up,
)

# Import cluster credentials - SGE or Slurm scheduling system
from mle_toolbox import mle_config

# Overview of implemented remote resources in addition to local processes
cluster_resources = ["sge-cluster", "slurm-cluster"]
cloud_resources = ["gcp-cloud"]


class Job(object):
    """
    Basic Job Class - Everything builds on this!

    This class defines, executes & monitors an individual job that can
    either be run locally, on a sungrid-engine (SGE) or SLURM cluster.

    Args:
        resource_to_run (str): Compute resource to execute job on.

        job_filename (str): filepath to .py script to be executed for job.

        config_filename (str): filepath to .json file specifying configuration
            of experiment to be executed in this job.

        job_arguments (dict): ressources required for this specific job.

        experiment_dir (str): set path for logging & unique storage of results.

        cmd_line_input (dict): provides standardized cmd input to .py file in
            job submission. Includes -config, -exp_dir, -seed.

        extra_cmd_line_input (dict): provides additional cmd input .py file
            in job submission. Dictionary should be structured so that input
            are passed as -<key> <value>.

        logger_level (str): control logger verbosity of individual experiment.

    Methods:
        run: Executes job, logs it & returns status if job done
        schedule: Schedules job locally or remotely
        schedule_local: Schedules job locally on your machine
        schedule_cluster: Schedules job remotely on SGE/Slurm clusters
        monitor: Monitors job locally or remotely
        monitor_local: Monitors job locally on your machine
        monitor_cluster: Monitors job remotely on SGE/Slurm clusters
    """

    def __init__(
        self,
        resource_to_run: str,
        job_filename: str,
        config_filename: Union[None, str],
        job_arguments: dict = {},
        experiment_dir: str = "experiments/",
        cmd_line_input: Union[None, dict] = None,
        extra_cmd_line_input: Union[None, dict] = None,
        logger_level: int = logging.WARNING,
    ):
        # Init job class with relevant info
        self.resource_to_run = resource_to_run  # compute resource for job
        self.job_filename = job_filename  # path to train script
        self.config_filename = config_filename  # path to config json
        self.experiment_dir = experiment_dir  # main results dir (create)
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)

        # Check if all required args are given - otw. add default to copy
        self.job_arguments = self.check_job_args(job_arguments.copy())

        # Create command line arguments for job to schedule (passed to .py)
        self.cmd_line_args = self.generate_cmd_line_args(cmd_line_input)

        # Add additional cmd line args if extra ones are specified
        if extra_cmd_line_input is not None:
            self.cmd_line_args = self.generate_extra_cmd_line_args(
                self.cmd_line_args, extra_cmd_line_input.copy()
            )

        # Instantiate/connect a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logger_level)

    def check_job_args(self, job_arguments):
        """Check if required args are provided. Complete w. default otw."""
        if self.resource_to_run == "sge-cluster":
            full_job_arguments = sge_check_job_args(job_arguments)
        elif self.resource_to_run == "slurm-cluster":
            full_job_arguments = slurm_check_job_args(job_arguments)
        elif self.resource_to_run == "gcp-cloud":
            full_job_arguments = gcp_check_job_args(job_arguments)
        else:
            full_job_arguments = local_check_job_args(job_arguments)
        return full_job_arguments

    def run(self) -> bool:
        """Schedule experiment, monitor and clean up afterwards."""
        # Schedule job, create success boolean and job identifier
        job_id = self.schedule()
        # Monitor status of job based on identifier
        status_out = self.monitor(job_id, continuous=True)
        # If they exist - remove log & error file
        self.clean_up(job_id)
        return status_out

    def schedule(self) -> str:
        """Schedule job on cluster (sge/slurm), cloud (gcp) or locally."""
        if self.resource_to_run in cluster_resources:
            job_id = self.schedule_cluster()
            if self.job_status == 1:
                self.logger.info(
                    f"Job ID: {job_id} - Cluster job scheduled"
                    f" - {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"Job ID: {job_id} - Error when scheduling "
                    f"cluster job - {self.config_filename}"
                )
        elif self.resource_to_run in cloud_resources:
            job_id = self.schedule_cloud()
            if self.job_status == 1:
                self.logger.info(
                    f"VM Name: {job_id} - Cloud job scheduled"
                    f" - {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"VM Name: {job_id} - Error when scheduling "
                    f"cloud job - {self.config_filename}"
                )
        else:
            job_id = self.schedule_local()
            if self.job_status == 1:
                self.logger.info(
                    f"PID: {job_id.pid} - Local job scheduled "
                    f"- {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"PID: {job_id.pid} - Error when scheduling "
                    f"local job - {self.config_filename}"
                )
        # Return sge/slurm - job_id (qstat/squeue), gcp - vm_name, local - proc
        return job_id

    def monitor(self, job_id: str, continuous: bool = True) -> bool:
        """
        Monitor on cluster (sge/slurm), cloud (gcp) or locally via id.
        If 'continuous' bool is true, then monitor until experiment status 0.
        """
        if self.resource_to_run in cluster_resources:
            status_out = self.monitor_cluster(job_id, continuous)
            if status_out == 0:
                self.logger.info(
                    f"Job ID: {job_id} - "
                    "Cluster job successfully "
                    f"completed - {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"Job ID: {job_id} - Error when running "
                    f"cluster job - {self.config_filename}"
                )
        elif self.resource_to_run in cloud_resources:
            status_out = self.monitor_cloud(job_id, continuous)
            if status_out == 0:
                self.logger.info(
                    f"VM Name: {job_id} - Cloud job successfully "
                    f"completed - {self.config_filename}"
                )
            else:
                self.logger.info(
                    f"VM Name: {job_id} - Error when running "
                    f"cloud job - {self.config_filename}"
                )
        else:
            status_out = self.monitor_local(job_id, continuous)
            if status_out == 0:
                self.logger.info(
                    "PID: {job_id.pid} - Local job successfully "
                    f"completed - { self.config_filename}"
                )
            else:
                self.logger.info(
                    f"PID: {job_id.pid} - Error when running "
                    f"local job - {self.config_filename}"
                )
        return status_out

    def schedule_local(self):
        """Schedules job locally on your machine."""
        if mle_config.general.use_conda_virtual_env:
            proc = local_submit_conda_job(
                self.job_filename, self.cmd_line_args, self.job_arguments
            )
        elif mle_config.general.use_venv_virtual_env:
            proc = local_submit_venv_job(
                self.job_filename, self.cmd_line_args, self.job_arguments
            )
        else:
            proc = local_submit_job(self.job_filename, self.cmd_line_args)
        self.job_status = 1
        return proc

    def schedule_cluster(self) -> int:
        """Schedules job to run remotely on SGE or Slurm clusters."""
        if self.resource_to_run == "sge-cluster":
            job_id = sge_submit_job(
                self.job_filename, self.cmd_line_args, self.job_arguments, clean_up=True
            )
        elif self.resource_to_run == "slurm-cluster":
            job_id = slurm_submit_job(
                self.job_filename, self.cmd_line_args, self.job_arguments, clean_up=True
            )
        if job_id == -1:
            self.job_status = 0
        else:
            self.job_status = 1
        return job_id

    def schedule_cloud(self) -> int:
        """Schedules job to run remotely on GCP cloud."""
        if self.resource_to_run == "gcp-cloud":
            # Import utility to copy local code directory to GCS bucket
            from mle_toolbox.remote.gcloud_transfer import upload_local_dir_to_gcs

            # Send config file to remote machine - independent of code base!
            upload_local_dir_to_gcs(
                local_path=self.config_filename,
                gcs_path=os.path.join(mle_config.gcp.code_dir, self.config_filename),
            )

            # Submit VM Creation + Startup exec
            job_id = gcp_submit_job(
                self.job_filename,
                self.cmd_line_args,
                self.job_arguments,
                self.experiment_dir,
                clean_up=True,
            )
        if job_id == -1:
            self.job_status = 0
        else:
            self.job_status = 1
        return job_id

    def monitor_local(self, proc, continuous: bool = True) -> int:
        """Monitors job locally on your machine."""
        # Poll status of local process & change status when done
        if continuous:
            while self.job_status:
                poll = proc.poll()
                if poll is None:
                    continue
                else:
                    self.job_status = 0
                # Sleep until next status check
                time.sleep(1)

            # Get output & error messages (if there is an error)
            out, err = proc.communicate()
            # Return -1 if job failed & 0 otherwise
            if proc.returncode != 0:
                print(out, err)
                return -1
            else:
                return 0
        else:
            poll = proc.poll()
            if poll is None:
                return 1
            else:
                return 0

    def monitor_cluster(self, job_id: str, continuous: bool = True) -> int:
        """Monitors job remotely on SGE or Slurm clusters."""
        if continuous:
            while self.job_status:
                if self.resource_to_run == "sge-cluster":
                    self.job_status = sge_monitor_job(job_id)
                elif self.resource_to_run == "slurm-cluster":
                    self.job_status = slurm_monitor_job(job_id)
                time.sleep(1)
            return 0
        else:
            if self.resource_to_run == "sge-cluster":
                return sge_monitor_job(job_id)
            elif self.resource_to_run == "slurm-cluster":
                return slurm_monitor_job(job_id)

    def monitor_cloud(self, job_id: str, continuous: bool = True) -> int:
        """Monitors job remotely on GCP cloud."""
        if continuous:
            while self.job_status:
                if self.resource_to_run == "gcp-cloud":
                    self.job_status = gcp_monitor_job(job_id, self.job_arguments)
                time.sleep(10)
            return 0
        else:
            if self.resource_to_run == "gcp-cloud":
                return gcp_monitor_job(job_id, self.job_arguments)

    def clean_up(self, job_id: str) -> None:
        """Remove error and log files at end of training."""
        for filename in glob.glob(self.job_arguments["err_file"] + "*"):
            try:
                os.remove(filename)
            except Exception:
                pass
        for filename in glob.glob(self.job_arguments["log_file"] + "*"):
            try:
                os.remove(filename)
            except Exception:
                pass
        self.logger.info("Cleaned up log, error, results files")

        # Delete VM instance and code directory stored in data bucket
        if self.resource_to_run == "gcp-cloud":
            gcp_clean_up(job_id, self.job_arguments, self.experiment_dir)
            # Wait for download to wrap up!
            time.sleep(100)

    def generate_cmd_line_args(self, cmd_line_input: Union[None, dict] = None) -> str:
        """Generate cmd line args for .py -> get_train_configs_ready"""
        cmd_line_args = " -exp_dir " + self.experiment_dir

        if self.config_filename is not None:
            cmd_line_args += " -config " + self.config_filename

        if cmd_line_input is not None:
            if "seed_id" in cmd_line_input.keys():
                cmd_line_args += " -seed " + str(cmd_line_input["seed_id"])
                # Update the job argument details with the seed-job-id
                self.job_arguments["job_name"] += "-" + str(cmd_line_input["seed_id"])
            if "model_ckpt" in cmd_line_input.keys():
                cmd_line_args += " -model_ckpt " + str(cmd_line_input["model_ckpt"])
        return cmd_line_args

    def generate_extra_cmd_line_args(
        self, cmd_line_args: str, extra_cmd_line_input: Union[None, dict] = None
    ) -> str:
        """Generate extra cmd line args for .py -> e.g. for postproc"""
        full_cmd_line_args = (cmd_line_args + ".")[:-1]
        if extra_cmd_line_input is not None:
            for k, v in extra_cmd_line_input.items():
                full_cmd_line_args += " -" + k + " " + str(v)
        return full_cmd_line_args
