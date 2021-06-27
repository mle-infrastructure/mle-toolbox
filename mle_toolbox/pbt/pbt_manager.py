import os
import copy
import json
import shutil
import logging
from typing import Union
import numpy as np

from mle_toolbox.experiment import Experiment
from ..utils import load_json_config
from .pbt_logger import PBT_Logger
from .explore import ExplorationStrategy
from .exploit import SelectionStrategy


class PBT_Manager(object):
    def __init__(self,
                 pbt_log: PBT_Logger,
                 resource_to_run: str,
                 job_arguments: dict,
                 config_fname: str,
                 job_fname: str,
                 experiment_dir: str,
                 pbt_resources: dict,
                 pbt_config: dict,
                 logger_level: int=logging.WARNING):
        """ Manger orchestrating PBT experiment """
        # Set up the PBT search run
        self.pbt_log = pbt_log                        # Hyperopt. Log Instance
        self.resource_to_run = resource_to_run        # Compute resource to run
        self.config_fname = config_fname              # Fname base config file
        self.base_config = load_json_config(config_fname)  # Base Train Config
        self.job_fname = job_fname                    # Python file to run job
        self.job_arguments = job_arguments            # Cluster/VM job info
        self.experiment_dir = experiment_dir          # Where to store all logs
        if self.experiment_dir[-1] != "/":
            self.experiment_dir += "/"

        # Create the directory if it doesn't exist yet
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)

        # Copy over base config .json file -  to be copied + modified in search
        config_copy = os.path.join(self.experiment_dir, "pbt_base_config.json")
        if not os.path.exists(config_copy):
            shutil.copy(config_fname, config_copy)

        # Instantiate/connect a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logger_level)

        # PBT-specific arguments
        self.pbt_resources = pbt_resources
        self.pbt_config = pbt_config
        #self.num_pbt_step

        # Setup the exploration and selection strategies
        self.exploration = ExplorationStrategy(pbt_config.exploration.strategy,
                                               pbt_config.pbt_params)
        self.selection = SelectionStrategy(pbt_config.selection.strategy)

    def run(self):
        """ Run the PBT Hyperparameter Search. """
        self.num_running_jobs = 0     # No. concurrently running jobs/workers
        self.pbt_queue = []
        # Launch a first set of jobs - sample from prior distribution
        for worker_id in range(self.pbt_resources.num_population_members):
            hyperparams = self.exploration.resample()
            print(hyperparams)
            seed_id = np.random.randint(1000, 9999)
            config_fname = self.save_config(worker_id, 0, hyperparams)
            #experiment, job_id = self.launch(config_fname, seed_id)
            # self.pbt_queue.append({"worker_id": worker_id,
            #                        "pbt_step_id": 0,
            #                        "experiment": experiment,
            #                        "job_id": job_id,
            #                        "seed_id": seed_id,
            #                        "hyperparams": hyperparams})
            self.num_running_jobs += 1
        return

    def launch(self, config_fname: str, seed_id: int,
               model_ckpt: Union[None, str]=None):
        """ Launch a set of jobs for one configuration and network checkpoint. """
        # 1. Instantiate the experiment class and start a single seed
        cmd_line_input = {"seed_id": seed_id}
        if model_ckpt is not None:
            cmd_line_input["model_ckpt"] = model_ckpt
        experiment = Experiment(self.resource_to_run,
                                self.job_filename,
                                config_fname,
                                self.job_arguments,
                                self.experiment_dir,
                                cmd_line_input)

        # 2. Launch a single experiment
        job_id = experiment.schedule()

        # 3. Return updated counter, `Experiment` instance & corresponding ID
        return experiment, job_id

    def monitor(self, experiment: Experiment, job_id: str):
        """ Monitor job for one eval/worker configuration. """
        status = experiment.monitor(job_id, False)
        return status

    def save_config(self, worker_id: int, pbt_step_id: int, hyperparams: dict):
        """ Generate config file for a specific proposal to evaluate """
        sample_config = copy.deepcopy(self.base_config)

        # Construct config dicts individually - set params in train config
        for param_name, param_value in hyperparams.items():
            sample_config.train_config[param_name] = param_value

        # Write hyperparams to config .json
        run_id = "worker_" + str(worker_id) + "_step_" + str(pbt_step_id)
        s_config_fname = os.path.join(self.experiment_dir, run_id + '.json')
        with open(s_config_fname, 'w') as f:
            json.dump(sample_config, f)
        return s_config_fname
