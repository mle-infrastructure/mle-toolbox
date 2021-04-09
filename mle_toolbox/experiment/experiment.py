import os
import re
import glob
import time
import platform
import logging
from typing import Union
import subprocess as sp

from .manage_local_job import (local_check_job_args,
                               local_submit_venv_job,
                               local_submit_conda_job)
from .manage_sge_job import (sge_check_job_args,
                             sge_submit_remote_job,
                             sge_monitor_remote_job)
from .manage_slurm_job import (slurm_check_job_args,
                               slurm_submit_remote_job,
                               slurm_monitor_remote_job)

# Import cluster credentials - SGE or Slurm scheduling system
from ..utils import load_mle_toolbox_config

cc = load_mle_toolbox_config()


class Experiment(object):
    """
    Basic Experiment Class - Everything builds on this!

    This class defines, executes & monitors an individual experiment that can
    either be run locally, on a sungrid-engine (SGE) or SLURM cluster.

    Args:
        job_filename (str): filepath to .py script to be executed for job.

        config_filename (str): filepath to .json file specifying configuration
            of experiment to be executed in this job.

        job_arguments (dict): ressources required for this specific job.

        experiment_dir (str): sets path for logging & unique storage of results.

        cmd_line_input (dict): provides standardized cmd input to .py file in job submission.
            Includes -config, -exp_dir, -seed.

        extra_cmd_line_input (dict): provides additional cmd input .py file in job submission.
            Dictionary should be structured so that input are passed as -<key> <value>.

        logger_level (str): control logger verbosity of individual experiment.

    Methods:
        run: Executes experiment, logs it & returns status if experiment done
        schedule: Schedules experiment locally or remotely
        schedule_local: Schedules experiment locally on your machine
        schedule_remote: Schedules experiment remotely on SGE/Slurm clusters
        monitor: Monitors experiment locally or remotely
        monitor_local: Monitors experiment locally on your machine
        monitor_remote: Monitors experiment remotely on SGE/Slurm clusters
    """
    def __init__(self,
                 job_filename: str,
                 config_filename: Union[None, str],
                 job_arguments: Union[None, dict],
                 experiment_dir: str,
                 cmd_line_input: Union[None, dict]=None,
                 extra_cmd_line_input: Union[None, dict]=None,
                 logger_level: str=logging.WARNING):
        # Init experiment class with relevant info
        self.job_filename = job_filename           # path to train script
        self.config_filename = config_filename     # path to config json

        # Create the main experiment directory if it doesn't exist yet
        self.experiment_dir = experiment_dir
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)

        # Check the availability of the cluster to run job
        self.run_on_remote = self.cluster_available()

        # Check if all required args are given - otw. add default
        if self.run_on_sge_cluster:
            self.job_arguments = sge_check_job_args(job_arguments)
        elif self.run_on_slurm_cluster:
            self.job_arguments = slurm_check_job_args(job_arguments)
        else:
            self.job_arguments = local_check_job_args(job_arguments)

        # Create command line arguments for job to schedule (passed to .py)
        self.cmd_line_args = self.generate_cmd_line_args(cmd_line_input)

        # Add additional cmd line args if extra ones are specified
        if extra_cmd_line_input is not None:
            self.cmd_line_args = self.generate_extra_cmd_line_args(self.cmd_line_args,
                                                                   extra_cmd_line_input)

        # Instantiate/connect a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logger_level)

    def run(self):
        """ Exec experiment, logs & returns status if experiment done. """
        # Schedule the job, return its identifier & monitor job status
        if self.run_on_remote:
            job_id = self.schedule_remote()
            if self.job_status == 1:
                self.logger.info(f"Job ID: {job_id} - Remote job scheduled" \
                                  " - {self.config_filename}")
            else:
                self.logger.info(f"Job ID: {job_id} - Error when scheduling " \
                                 f"remote job - {self.config_filename}")
            status_out = self.monitor_remote(job_id)
            if status_out == 0:
                self.logger.info(f"Job ID: {job_id} - Remote job successfully " \
                                 f"completed - {self.config_filename}")
            else:
                self.logger.info(f"Job ID: {job_id} - Error when running " \
                                 f"remote job - {self.config_filename}")
        else:
            proc = self.schedule_local()
            if self.job_status == 1:
                self.logger.info(f"PID: {proc.pid} - Local job scheduled " \
                                 f"- {self.config_filename}")
            else:
                self.logger.info(f"PID: {proc.pid} - Error when scheduling local " \
                                 f"job - {self.config_filename}")
            status_out = self.monitor_local(proc)
            if status_out == 0:
                self.logger.info("PID: {proc.pid} - Local job successfully " \
                                 "completed - { self.config_filename}")
            else:
                self.logger.info(f"PID: {proc.pid} - Error when running local " \
                                 f"job - {self.config_filename}")

        # If they exist - remove qsub log & error file
        self.clean_up()
        return status_out

    def schedule_local(self):
        """ Schedules experiment locally on your machine. """
        if cc.general.use_conda_virtual_env:
            proc = local_submit_conda_job(self.job_filename,
                                          self.cmd_line_args,
                                          self.job_arguments)
        else:
            proc = local_submit_venv_job(self.job_filename,
                                         self.cmd_line_args,
                                         self.job_arguments)
        self.job_status = 1
        return proc

    def schedule_remote(self):
        """ Schedules experiment to run remotely on SGE. """
        if self.run_on_sge_cluster:
            job_id = sge_submit_remote_job(self.job_filename,
                                           self.cmd_line_args,
                                           self.job_arguments,
                                           clean_up=True)
        elif self.run_on_slurm_cluster:
            job_id = slurm_submit_remote_job(self.job_filename,
                                             self.cmd_line_args,
                                             self.job_arguments,
                                             clean_up=True)

        if job_id == -1:
            self.job_status = 0
        else:
            self.job_status = 1

        return job_id

    def monitor_local(self, proc):
        """ Monitors experiment locally on your machine. """
        # Poll status of local process & change status when done
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

    def monitor_remote(self, job_id):
        """ Schedules experiment remotely on SGE. """
        while self.job_status:
            if self.run_on_sge_cluster:
                self.job_status = sge_monitor_remote_job(job_id)
            elif self.run_on_slurm_cluster:
                self.job_status = slurm_monitor_remote_job(job_id)
            time.sleep(1)
        return 0

    def cluster_available(self):
        """ Check if cluster (sge/slurm) is available or only local run. """
        hostname = platform.node()
        on_sge_cluster = any(re.match(l, hostname) for l in cc.sge.info.node_reg_exp)
        on_slurm_cluster = any(re.match(l, hostname) for l in cc.slurm.info.node_reg_exp)
        on_sge_head = (hostname in cc.sge.info.head_names)
        on_slurm_head = (hostname in cc.slurm.info.head_names)
        if on_sge_head or on_sge_cluster:
            self.run_on_sge_cluster = 1
            self.run_on_slurm_cluster = 0
        elif on_slurm_head or on_slurm_cluster:
            self.run_on_sge_cluster = 0
            self.run_on_slurm_cluster = 1
        else:
            self.run_on_sge_cluster = 0
            self.run_on_slurm_cluster = 0
        return on_sge_cluster or on_sge_head or on_slurm_head or on_slurm_cluster

    def generate_cmd_line_args(self,
                               cmd_line_input: Union[None, dict]=None) -> str:
        """ Generate cmd line args for .py -> get_train_configs_ready """
        cmd_line_args = " -exp_dir " + self.experiment_dir

        if self.config_filename is not None:
            cmd_line_args += " -config " + self.config_filename

        if cmd_line_input is not None:
            if "seed_id" in cmd_line_input.keys():
                cmd_line_args += " -seed " + str(cmd_line_input["seed_id"])
                # Update the job argument details with the seed-job-id
                self.job_arguments["job_name"] += "-" + str(cmd_line_input["seed_id"])
        return cmd_line_args

    def generate_extra_cmd_line_args(self, cmd_line_args: str,
                                     extra_cmd_line_input: Union[None, dict]=None) -> str:
        """ Generate extra cmd line args for .py -> mainly for results postprocessing """
        full_cmd_line_args = (cmd_line_args + '.')[:-1]
        for k, v in extra_cmd_line_input.items():
            full_cmd_line_args += " -" + k + " " + str(v)
        return full_cmd_line_args

    def clean_up(self):
        """ Remove error and log files at end of training. """
        # Clean up if not development!
        if not cc.general.development:
            for filename in glob.glob(self.job_arguments["err_file"] + "*"):
                try: os.remove(filename)
                except: pass
            for filename in glob.glob(self.job_arguments["log_file"] + "*"):
                try: os.remove(filename)
                except: pass
            self.logger.info("Cleaned up log, error, results files")
