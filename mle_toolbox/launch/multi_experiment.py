import logging
from ..experiment import spawn_multiple_configs


def run_multiple_experiments(resource_to_run: str,
                             meta_job_args: dict,
                             single_job_args: dict,
                             multi_experiment_args: dict):
    """ Run an experiment over different configurations (+random seeds). """
    # 1. Create multiple experiment instances and submit the jobs
    spawn_multiple_configs(resource_to_run,
                           meta_job_args.base_train_fname,
                           multi_experiment_args.config_fnames,
                           single_job_args,
                           meta_job_args.experiment_dir,
                           num_seeds=multi_experiment_args.num_seeds,
                           logger_level=logging.INFO)
