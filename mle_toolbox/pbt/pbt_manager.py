import os
import shutil


class PBT_Manager(object):
    def __init__(self,
                 pbt_log: PBT_Logger,
                 resource_to_run: str,
                 job_arguments: dict,
                 config_fname: str,
                 job_fname: str,
                 experiment_dir: str,
                 pbt_params: dict):
        """ """
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

        # Key Input: Specify which params to optimize & in which ranges (dict)
        self.pbt_params = pbt_params            # exploration/exploitation

    def run(self):
        return
