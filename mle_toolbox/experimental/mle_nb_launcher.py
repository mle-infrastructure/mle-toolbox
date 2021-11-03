from mle_toolbox.launch import (
    run_single_config,
    run_processing_job,
    run_multiple_configs,
    run_hyperparameter_search,
)


class MLE_NBLaucnher(object):
    def __init__(
        self,
        resource_name: str,
        meta_job_args: dict,
        experiment_args: dict,
        single_job_args: dict,
    ):
        """Helper for launching experiments from a notebook."""
        self.resource_name = resource_name
        self.meta_job_args = meta_job_args
        self.experiment_args = experiment_args
        self.single_job_args = single_job_args

    def launch(self):
        # (a) Experiment: Run a single experiment
        if self.meta_job_args["experiment_type"] == "single-config":
            run_single_config(
                self.resource_name, self.meta_job_args, self.single_job_args
            )

        # (b) Experiment: Run training over different config files/seeds
        elif self.meta_job_args["experiment_type"] == "multiple-configs":
            run_multiple_configs(
                self.resource_name,
                self.meta_job_args,
                self.single_job_args,
                self.multi_config_args,
            )
        # (c) Experiment: Run hyperparameter search (Random, Grid, SMBO)
        elif self.meta_job_args["experiment_type"] == "hyperparameter-search":
            run_hyperparameter_search(
                self.resource_name,
                self.meta_job_args,
                self.single_job_args,
                self.experiment_args,
            )
        # (d) Experiment: Run population-based-training for NN training
        elif self.meta_job_args["experiment_type"] == "population-based-training":
            from ..experimental.pbt_experiment import run_population_based_training

            run_population_based_training(
                self.resource_name,
                self.meta_job_args,
                self.single_job_args,
                self.experiment_args,
            )
