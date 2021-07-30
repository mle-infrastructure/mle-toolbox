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
from ..utils import load_json_config, load_run_log
from .pbt_logger import PBT_Logger, Population_Logger
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
        """Manger orchestrating PBT experiment"""
        # Set up the PBT search run
        self.pbt_log = pbt_log  # Hyperopt. Log Instance
        self.resource_to_run = resource_to_run  # Compute resource to run
        self.config_fname = config_fname  # Fname base config file
        self.base_config = load_json_config(config_fname)  # Base Train Config
        self.job_fname = job_fname  # Python file to run job
        self.job_arguments = job_arguments  # Cluster/VM job info
        self.experiment_dir = experiment_dir  # Where to store all logs
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
        self.num_population_members = pbt_resources["num_population_members"]
        self.num_total_update_steps = pbt_resources["num_total_update_steps"]
        self.num_steps_until_ready = pbt_resources["num_steps_until_ready"]
        self.num_steps_until_eval = pbt_resources["num_steps_until_eval"]
        self.num_pbt_steps = math.ceil(
            self.num_total_update_steps / self.num_steps_until_ready  # noqa: W504,E501
        )

        # Setup the exploration and selection strategies
        self.gen_logger = Population_Logger(
            pbt_logging["eval_metric"],
            pbt_logging["max_objective"],
            self.num_population_members,
        )
        self.selection = SelectionStrategy(pbt_config["selection"]["strategy"])
        self.exploration = ExplorationStrategy(
            pbt_config["exploration"]["strategy"], pbt_config["pbt_params"]
        )

    def run(self):
        """Run the PBT Hyperparameter Search."""
        self.pbt_queue = []
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
            run_id, config_fname = self.save_config(worker_id, 0, hyperparams)
            job, job_id = self.launch(config_fname, seed_id)
            self.pbt_queue.append(
                {
                    "worker_id": worker_id,
                    "pbt_step_id": 0,
                    "job": job,
                    "config_fname": config_fname,
                    "job_id": job_id,
                    "run_id": run_id,
                    "seed_id": seed_id,
                    "hyperparams": hyperparams,
                }
            )
            time.sleep(0.1)

        self.logger.info("LAUNCH - First PBT Batch: " f"{self.num_population_members}")
        population_bars = [
            tqdm(
                total=self.num_pbt_steps,
                position=i,
                leave=True,
                bar_format="{l_bar}{bar:45}{r_bar}{bar:-45b}",
            )
            for i in range(self.num_population_members)
        ]

        # Monitor - exploit, explore
        while True:
            completed_pbt = 0
            for w_id in range(self.num_population_members):
                worker = self.pbt_queue[w_id]
                status = self.monitor(worker["job"], worker["job_id"])

                if status == 0:
                    try:
                        os.remove(worker["config_fname"])
                    except Exception:
                        pass

                    # 0. Update progress bar for worker
                    population_bars[worker["worker_id"]].update(1)

                    # 1. Load logs & checkpoint paths + update pbt log
                    worker_logs = self.get_pbt_log_data()
                    self.gen_logger.update_log(worker_logs)

                    if worker["pbt_step_id"] < self.num_pbt_steps - 1:
                        # 2. Exploit/Selection step
                        copy_info, hyperparams, ckpt = self.selection.select(
                            worker["worker_id"], self.gen_logger
                        )
                        print(hyperparams)
                        # 3. Exploration if previous exploitation update
                        if copy_info["copy_bool"]:
                            hyperparams = self.exploration.explore(hyperparams)

                        # 4. Spawn a new job
                        seed_id = np.random.randint(1000, 9999)
                        run_id, config_fname = self.save_config(
                            worker["worker_id"], worker["pbt_step_id"] + 1, hyperparams
                        )
                        job, job_id = self.launch(config_fname, seed_id, ckpt)
                        new_worker = {
                            "worker_id": worker["worker_id"],
                            "pbt_step_id": worker["pbt_step_id"] + 1,
                            "job": job,
                            "config_fname": config_fname,
                            "job_id": job_id,
                            "run_id": run_id,
                            "seed_id": seed_id,
                            "hyperparams": hyperparams,
                        }
                        time.sleep(0.1)

                        # Replace old worker by new one
                        self.pbt_queue[worker["worker_id"]] = new_worker
                    else:
                        population_bars[worker["worker_id"]].close()

                    num_updates, performance = self.gen_logger.get_worker_data(
                        worker["worker_id"]
                    )

                    log_data = {
                        "worker_id": worker["worker_id"],
                        "pbt_step_id": worker["pbt_step_id"],
                        "num_updates": num_updates,
                        "performance": performance,
                        "hyperparams": worker["hyperparams"],
                    }
                    for k, v in copy_info.items():
                        log_data[k] = v

                    self.pbt_log.update_log(log_data)
                    completed_pbt += (
                        worker["pbt_step_id"] == self.num_pbt_steps - 1
                    )  # noqa: 503
                # Break out of while loop once all workers done
            if completed_pbt == self.num_population_members:
                break

        # Finally remove remaining config files
        for worker in self.pbt_queue:
            try:
                os.remove(worker["config_fname"])
            except Exception:
                pass
        return

    def launch(
        self, config_fname: str, seed_id: int, model_ckpt: Union[None, str] = None
    ):
        """Launch jobs for one configuration and network checkpoint."""
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

        # 3. Return updated counter, `job` instance & corresponding ID
        return job, job_id

    def monitor(self, job: Job, job_id: str):
        """Monitor job for one eval/worker configuration."""
        status = job.monitor(job_id, False)
        return status

    def save_config(self, worker_id: int, pbt_step_id: int, hyperparams: dict):
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
        return run_id, s_config_fname

    def get_pbt_log_data(self):
        """Get best recent model & performance for population members."""
        log_data = []
        for worker in self.pbt_queue:
            # Get path to experiment storage directory
            try:
                subdirs = [
                    f.path for f in os.scandir(self.experiment_dir) if f.is_dir()
                ]
                exp_dir = [f for f in subdirs if f.endswith(worker["run_id"])][0]
                log_dir = os.path.join(exp_dir, "logs")
                model_dir = os.path.join(exp_dir, "models", "final")

                # Load performance log of worker
                log_files = [
                    os.path.join(log_dir, f)
                    for f in os.listdir(log_dir)
                    if os.path.isfile(os.path.join(log_dir, f))
                ]
                log_file = [f for f in log_files if f.endswith(".hdf5")]
                if len(log_file) > 0:
                    perf_log = load_run_log(exp_dir)
                    perf = perf_log.stats[self.pbt_logging["eval_metric"]][-1]
                    num_updates = perf_log.time["num_updates"][-1]
                else:
                    continue

                # Get network checkpoint filename
                # TODO: Make this more general (not only torch) - .pt/.npy/etc.
                model_files = [
                    os.path.join(model_dir, f)
                    for f in os.listdir(model_dir)
                    if os.path.isfile(os.path.join(model_dir, f))
                ]
                model_ckpt = [f for f in model_files if f.endswith(".pt")]

                log_data.append(
                    {
                        "worker_id": worker["worker_id"],
                        "pbt_step_id": worker["pbt_step_id"],
                        "num_updates": num_updates,
                        "log_path": log_file[0] if len(log_file) > 0 else None,
                        "model_ckpt": (model_ckpt[0] if len(model_ckpt) > 0 else None),
                        self.pbt_logging["eval_metric"]: perf,
                        "hyperparams": worker["hyperparams"],
                    }
                )
            except Exception:
                continue
        return log_data
