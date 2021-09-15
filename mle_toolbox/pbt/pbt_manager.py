import os
import copy
import json
import math
import time
import shutil
import logging
from typing import Union, Dict
import numpy as np
from tqdm import tqdm

from mle_toolbox.job import Job
from mle_logging.utils import load_json_config, load_yaml_config
from mle_logging import load_log

from .pbt_logger import PBT_Logger
from .explore import ExplorationStrategy
from .exploit import SelectionStrategy


class PBT_Manager(object):
    def __init__(
        self,
        pbt_log: PBT_Logger,
        resource_to_run: str,
        job_arguments: Dict[str, Union[str, int]],
        config_fname: str,
        job_fname: str,
        experiment_dir: str,
        pbt_logging: Dict[str, Union[str, int]],
        pbt_resources: Dict[str, int],
        pbt_config: Dict[str, Union[str, int]],
    ):
        """Manager orchestrating PBT experiment"""
        # Set up the PBT search run
        self.pbt_log = pbt_log  # Hyperopt. Log Instance
        self.resource_to_run = resource_to_run  # Compute resource to run
        self.config_fname = config_fname  # Fname base config file
        fname, fext = os.path.splitext(config_fname)
        if fext == ".json":
            self.base_config = load_json_config(config_fname, return_dotmap=True)
        elif fext == ".yaml":
            self.base_config = load_yaml_config(config_fname, return_dotmap=True)
        else:
            raise ValueError("Job config has to be .json or .yaml file.")

        self.job_fname = job_fname  # Python file to run job
        self.job_arguments = job_arguments  # Cluster/VM job info
        self.experiment_dir = experiment_dir  # Where to store all logs
        if self.experiment_dir[-1] != "/":
            self.experiment_dir += "/"

        # Create the directory if it doesn't exist yet
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)

        # Copy over base config .json file -  to be copied + modified in search
        config_copy = os.path.join(self.experiment_dir, "pbt_base_config" + fext)
        if not os.path.exists(config_copy):
            shutil.copy(config_fname, config_copy)

        # Instantiate/connect a logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.message_id = None

        # PBT-specific arguments
        self.pbt_config = pbt_config
        self.pbt_logging = pbt_logging
        self.num_population_members = pbt_resources["num_population_members"]
        self.num_total_update_steps = pbt_resources["num_total_update_steps"]
        self.num_steps_until_ready = pbt_resources["num_steps_until_ready"]
        self.num_steps_until_eval = pbt_resources["num_steps_until_eval"]
        self.num_pbt_steps = math.ceil(
            self.num_total_update_steps / self.num_steps_until_ready
        )

        # Setup the exploration and selection strategies
        self.selection = SelectionStrategy(pbt_config["selection"]["strategy"])
        self.exploration = ExplorationStrategy(
            pbt_config["exploration"]["strategy"], pbt_config["pbt_params"]
        )

    def startup(self) -> None:
        """Spawn first set of workers with initial hyperparams."""
        self.pbt_queue = {}
        self.logger.info(
            f"START - PBT Members: {self.num_population_members}"
            f" - Updates: {self.num_pbt_steps}"
            f" - Train Updates: {self.num_total_update_steps}"
        )
        self.logger.info(
            "-> Steps Until PBT 'Ready': "
            f"{self.num_steps_until_ready}"
            " - Steps Until PBT 'Eval': "
            f"{self.num_steps_until_eval}"
        )

        # Launch a first set of jobs - sample from prior distribution
        for worker_id in range(self.num_population_members):
            hyperparams = self.exploration.init_hyperparams(worker_id)
            seed_id = np.random.randint(1000, 9999)
            pbt_step_id, model_ckpt = 0, None
            config_fname = self.save_config(worker_id, pbt_step_id, hyperparams)
            worker_data = self.launch(
                worker_id, pbt_step_id, config_fname, seed_id, model_ckpt, hyperparams
            )
            self.pbt_queue[worker_id] = worker_data
            time.sleep(0.1)

        self.logger.info("LAUNCH - First PBT Batch: " f"{self.num_population_members}")
        self.population_bars = [
            tqdm(
                total=self.num_pbt_steps,
                position=i,
                leave=True,
                bar_format="{l_bar}{bar:45}{r_bar}{bar:-45b}",
                desc=f"Worker {i}",
                unit="Job",
            )
            for i in range(self.num_population_members)
        ]
        return

    def run(self) -> None:
        """Run the PBT Hyperparameter Search."""
        # 1. Launch first batch of jobs with initial hyperparams
        self.startup()
        # 2. Continuously monitor + spawn new workers - Explore/exploit.
        time.sleep(2)
        self.monitor_and_spawn()
        # 3. Construct log of all workers and hyperparameters

    def monitor_and_spawn(self):
        """Continuously monitor and spawn new workers - Explore/exploit."""
        # Monitor all workers sequentially - exploit, explore checks
        while True:
            completed_pbt = 0
            # Loop over all workers in the population & check their status
            for w_id in range(self.num_population_members):
                worker = self.pbt_queue[w_id]

                # 1. Get most recent performance of worker & add it to log
                worker_log = self.pbt_log.get_worker_data(
                    worker["worker_id"], worker["pbt_step_id"], worker["hyperparams"]
                )
                self.pbt_log.update_log(worker_log, save=True)
                completed_pbt += (
                    worker["pbt_step_id"] == self.num_pbt_steps - 1
                    and worker_log["num_updates"] == self.num_steps_until_ready
                )

                status = self.monitor(worker["job"], worker["job_id"])

                # If worker completed job - clean up + spawn new one
                if (
                    status == 0
                    and worker_log["num_updates"] == self.num_steps_until_ready
                ):
                    try:
                        os.remove(worker["config_fname"])
                    except Exception:
                        pass

                    # 0. Update progress bar for worker
                    self.population_bars[worker["worker_id"]].update(1)

                    # 1. Load logs & checkpoint paths + update pbt log
                    if worker["pbt_step_id"] < self.num_pbt_steps - 1:
                        # 2. Exploit/Selection step
                        copy_info, hyperparams, model_ckpt = self.selection.select(
                            worker["worker_id"], self.pbt_log
                        )
                        # 3. Exploration if previous exploitation update
                        if copy_info["copy_bool"]:
                            hyperparams = self.exploration.explore(hyperparams)

                        # 4. Spawn a new job
                        seed_id = np.random.randint(1000, 9999)
                        config_fname = self.save_config(
                            worker["worker_id"], worker["pbt_step_id"] + 1, hyperparams
                        )
                        worker_data = self.launch(
                            worker["worker_id"],
                            worker["pbt_step_id"] + 1,
                            config_fname,
                            seed_id,
                            model_ckpt,
                            hyperparams,
                        )

                        # Replace old worker by new one
                        self.pbt_queue[worker_data["worker_id"]] = worker_data

                        # Add copy info to pbt log
                        copy_info["worker_id"] = worker["worker_id"]
                        copy_info["pbt_step_id"] = worker["pbt_step_id"]
                        self.pbt_log.update_trajectory(copy_info, save=True)
                    else:
                        self.population_bars[worker["worker_id"]].close()
            # Break out of while loop once all workers done
            if completed_pbt == self.num_population_members:
                break
        return

    def launch(
        self,
        worker_id: int,
        pbt_step_id: int,
        config_fname: str,
        seed_id: int,
        model_ckpt: Union[None, str],
        hyperparams: dict,
    ) -> dict:
        """Launch jobs for one configuration and network checkpoint."""
        run_id = "worker_" + str(worker_id) + "_step_" + str(pbt_step_id)
        # 1. Instantiate the job class and start a single seed
        cmd_line_input = {"seed_id": seed_id}
        if model_ckpt is not None:
            cmd_line_input["model_ckpt"] = model_ckpt
        job = Job(
            self.resource_to_run,
            self.job_fname,
            config_fname,
            self.job_arguments,
            self.experiment_dir,
            cmd_line_input,
        )

        # 2. Launch a single job
        job_id = job.schedule()

        # 3. Return worker data
        worker_data = {
            "worker_id": worker_id,
            "pbt_step_id": pbt_step_id,
            "job": job,
            "config_fname": config_fname,
            "job_id": job_id,
            "run_id": run_id,
            "seed_id": seed_id,
            "hyperparams": hyperparams,
        }

        # Sleep so that experiment dir + 1st log is created before monitoring
        while True:
            time.sleep(1)
            subdirs = [f.path for f in os.scandir(self.experiment_dir) if f.is_dir()]
            exp_dir = [f for f in subdirs if f.endswith(run_id)]
            try:
                _ = load_log(exp_dir[0])
                break
            except Exception:
                continue
        return worker_data

    def monitor(self, job: Job, job_id: str) -> bool:
        """Monitor job for one eval/worker configuration."""
        status = job.monitor(job_id, False)
        return status

    def save_config(self, worker_id: int, pbt_step_id: int, hyperparams: dict) -> str:
        """Generate config file for a specific proposal to evaluate"""
        sample_config = copy.deepcopy(self.base_config)

        # Add amount of steps until eval/ready to train config & worker id/pbt step id
        sample_config.train_config["num_steps_until_ready"] = self.num_steps_until_ready
        sample_config.train_config["num_steps_until_eval"] = self.num_steps_until_eval
        sample_config.train_config["worker_id"] = worker_id
        sample_config.train_config["pbt_step_id"] = pbt_step_id
        # Construct config dicts individually - set params in train config
        for param_name, param_value in hyperparams.items():
            sample_config.train_config[param_name] = param_value

        # Write hyperparams to config .json
        run_id = "worker_" + str(worker_id) + "_step_" + str(pbt_step_id)
        s_config_fname = os.path.join(self.experiment_dir, run_id + ".json")
        with open(s_config_fname, "w") as f:
            json.dump(sample_config, f)
        return s_config_fname
