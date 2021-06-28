import os
import copy
import json
import math
import time
import shutil
import logging
from typing import Union
import numpy as np
from tqdm import tqdm

from mle_toolbox.experiment import Experiment
from ..utils import load_json_config, load_run_log
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
                 pbt_logging: dict,
                 pbt_resources: dict,
                 pbt_config: dict):
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
        self.logger.setLevel(logging.INFO)

        # PBT-specific arguments
        self.pbt_config = pbt_config
        self.pbt_logging = pbt_logging
        self.num_population_members = pbt_resources.num_population_members
        self.num_total_update_steps = pbt_resources.num_total_update_steps
        self.num_steps_until_ready = pbt_resources.num_steps_until_ready
        self.num_steps_until_eval = pbt_resources.num_steps_until_eval
        self.num_pbt_steps = math.ceil(self.num_total_update_steps/
                                       self.num_steps_until_ready)

        # Setup the exploration and selection strategies
        self.selection = SelectionStrategy(pbt_config.selection.strategy)
        self.exploration = ExplorationStrategy(pbt_config.exploration.strategy,
                                               pbt_config.pbt_params)

    def run(self):
        """ Run the PBT Hyperparameter Search. """
        self.pbt_queue = []
        self.logger.info(f"START - PBT Members: {self.num_population_members}"
                         + f" - Updates: {self.num_pbt_steps}"
                         + f" - Train Updates: {self.num_total_update_steps}")
        self.logger.info(f"-> Steps Until PBT 'Ready': {self.num_steps_until_ready}"
                         + f" - Steps Until PBT 'Eval': {self.num_steps_until_eval}")

        # Launch a first set of jobs - sample from prior distribution
        for worker_id in range(self.num_population_members):
            hyperparams = self.exploration.resample()
            seed_id = np.random.randint(1000, 9999)
            run_id, config_fname = self.save_config(worker_id, 0, hyperparams)
            experiment, job_id = self.launch(config_fname, seed_id)
            self.pbt_queue.append({"worker_id": worker_id,
                                   "pbt_step_id": 0,
                                   "experiment": experiment,
                                   "config_fname": config_fname,
                                   "job_id": job_id,
                                   "run_id": run_id,
                                   "seed_id": seed_id,
                                   "hyperparams": hyperparams})
            time.sleep(0.2)

        self.logger.info(f"LAUNCH - First PBT Batch: {self.num_population_members}")
        population_bars = [tqdm(total=self.num_pbt_steps, position=i,
                                bar_format='{l_bar}{bar:45}{r_bar}{bar:-45b}')
                           for i in range(self.num_population_members)]

        # Monitor - exploit, explore
        while True:
            completed_pbt = 0
            for w_id in range(self.num_population_members):
                worker = self.pbt_queue[w_id]
                status = self.monitor(worker["experiment"], worker["job_id"])

                if status == 0:
                    try:
                        os.remove(worker["config_fname"])
                    except:
                        pass
                    # 0. Update progress bar for worker
                    population_bars[worker["worker_id"]].update(1)

                    # 1. Load logs & checkpoint paths + update pbt log
                    worker_logs = self.get_pbt_log_data()
                    self.pbt_log.update_log(worker["worker_id"], worker_logs)

                    if worker["pbt_step_id"] < self.num_pbt_steps - 1:
                        # 2. Exploit/Selection step
                        copy_bool, hyperparams, ckpt = self.selection.select(
                                                            worker["worker_id"],
                                                            self.pbt_log)
                        # 3. Exploration if previous exploitation update
                        if copy_bool:
                            hyperparams = self.exploration.explore(hyperparams)

                        # 4. Spawn a new job
                        seed_id = np.random.randint(1000, 9999)
                        run_id, config_fname = self.save_config(
                                            worker["worker_id"],
                                            worker["pbt_step_id"] + 1,
                                            hyperparams)
                        experiment, job_id = self.launch(config_fname, seed_id,
                                                         ckpt)
                        new_worker = {"worker_id": worker["worker_id"],
                                      "pbt_step_id": worker["pbt_step_id"] + 1,
                                      "experiment": experiment,
                                      "config_fname": config_fname,
                                      "job_id": job_id,
                                      "run_id": run_id,
                                      "seed_id": seed_id,
                                      "hyperparams": hyperparams}
                        time.sleep(0.2)

                        # Replace old worker by new one
                        self.pbt_queue[w_id] = new_worker
                    else:
                        population_bars[w_id].close()

                    completed_pbt += 1
                # Break out of while loop once all workers done
            if completed_pbt == self.num_population_members:
                break

        # Finally remove remaining config files
        for worker in self.pbt_queue:
            try:
                os.remove(worker["config_fname"])
            except:
                pass
        return

    def launch(self, config_fname: str, seed_id: int,
               model_ckpt: Union[None, str]=None):
        """ Launch jobs for one configuration and network checkpoint. """
        # 1. Instantiate the experiment class and start a single seed
        cmd_line_input = {"seed_id": seed_id}
        if model_ckpt is not None:
            cmd_line_input["model_ckpt"] = model_ckpt
        experiment = Experiment(self.resource_to_run,
                                self.job_fname,
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

        # Add amount of steps until eval/ready to train config
        sample_config.train_config["num_steps_until_ready"] = self.num_steps_until_ready
        sample_config.train_config["num_steps_until_eval"] = self.num_steps_until_eval

        # Construct config dicts individually - set params in train config
        for param_name, param_value in hyperparams.items():
            sample_config.train_config[param_name] = param_value

        # Write hyperparams to config .json
        run_id = "worker_" + str(worker_id) + "_step_" + str(pbt_step_id)
        s_config_fname = os.path.join(self.experiment_dir, run_id + '.json')
        with open(s_config_fname, 'w') as f:
            json.dump(sample_config, f)
        return run_id, s_config_fname

    def get_pbt_log_data(self):
        """ Get best recent model & performance for population members. """
        log_data = []
        for worker in self.pbt_queue:
            # Get path to experiment storage directory
            try:
                subdirs = [f.path for f in os.scandir(self.experiment_dir) if f.is_dir()]
                exp_dir = [f for f in subdirs if f.endswith(worker["run_id"])][0]
                log_dir = os.path.join(exp_dir, "logs")
                model_dir = os.path.join(exp_dir, "models", "final")

                # Load performance log of worker
                log_files = [os.path.join(log_dir, f) for f in os.listdir(log_dir)
                             if os.path.isfile(os.path.join(log_dir, f))]
                log_file = [f for f in log_files if f.endswith(".hdf5")]

                if len(log_file) > 0:
                    perf_log = load_run_log(exp_dir)
                    perf = perf_log.meta_log.stats[self.pbt_logging.eval_metric][-1]
                    num_updates = perf_log.meta_log.time["num_updates"][-1]
                else:
                    continue

                # Get network checkpoint filename - TODO: general - .pt/.npy/etc.
                model_files = [os.path.join(model_dir, f) for f in os.listdir(model_dir)
                               if os.path.isfile(os.path.join(model_dir, f))]
                model_ckpt = [f for f in model_files if f.endswith(".pt")]

                log_data.append({
                    "worker_id": worker["worker_id"],
                    "pbt_step_id": worker["pbt_step_id"],
                    "num_updates": num_updates,
                    "log_path": log_file[0] if len(log_file) > 0 else None,
                    "model_ckpt": model_ckpt[0] if len(model_ckpt) > 0 else None,
                    self.pbt_logging.eval_metric: perf,
                    "hyperparams": worker["hyperparams"]})
            except:
                continue
        return log_data
