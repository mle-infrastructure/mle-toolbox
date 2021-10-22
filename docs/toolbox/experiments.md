# Experiment Types

*Note*: This page and content is still work in progress!

## Pre-/Post-Processing

```yaml
# Parameters for the pre-processing job
pre_processing_args:
    processing_fname: "<run_preprocessing>.py"
    processing_job_args:
        num_logical_cores: 2
        time_per_job: "00:01:00"
    extra_cmd_line_input:
        figures_dir: "experiments/data"

# Parameters for the post-processing job
post_processing_args:
    processing_fname: "<run_postprocessing>.py"
    processing_job_args:
        num_logical_cores: 2
        time_per_job: "00:01:00"
    extra_cmd_line_input:
        figures_dir: "experiments/figures"
```


## Multiple Configurations & Seeds

```yaml
multi_config_args:
    config_fnames:
        - "config_1.json"
        - "config_2.json"
    num_seeds: 2
```


## Hyperparameter Search

Given a fixed training configuration file and the Python training script the only thing that has to be adapted for the different types of experiments is the meta configuration file.

```yaml
# Parameters specific to the hyperparameter search
param_search_args:
    search_logging:
        reload_log: False
        verbose_log: True
        max_objective: True
        problem_type: "final"
        eval_metrics: "test_loss"
    search_resources:
        num_search_batches: 2
        num_evals_per_batch: 2
        num_seeds_per_eval: 1
    search_config:
        search_type: "grid"  # "random"/"smbo"
        search_schedule: "sync"
        search_params:
            categorical:
                opt_type:
                    - "Adam"
                    - "RMSprop"
            real:
                l_rate:
                    begin: 1e-5
                    end: 1e-2
                    bins: 2
```


## Population-Based Training


```yaml
# Parameters specific to the population-based training
pbt_args:
    pbt_logging:
        max_objective: False
        eval_metric: "test_loss"
    pbt_resources:
        num_population_members: 10
        num_total_update_steps: 2000
        num_steps_until_ready: 500
        num_steps_until_eval: 100
    pbt_config:
        pbt_params:
            real:
                l_rate:
                    begin: 1e-5
                    end: 1e-2
        exploration:
            strategy: "perturb"
        selection:
            strategy: "truncation"
```
