from ..experiment import Experiment


def run_single_experiment(resource_to_run: str,
                          meta_job_args: dict,
                          single_job_args: dict):
    """ Run a single experiment locally/remote. """
    # 1. Instantiate the experiment class
    experiment = Experiment(resource_to_run,
                            meta_job_args.base_train_fname,
                            meta_job_args.base_train_config,
                            single_job_args,
                            meta_job_args.experiment_dir)
    # 2. Run the single experiment
    status_out = experiment.run()
