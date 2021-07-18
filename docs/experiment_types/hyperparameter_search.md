# Hyperparameter Searches

*Note*: This page and content is still work in progress!

Given a fixed training configuration file and the Python training script the only thing that has to be adapted for the different types of experiments is the meta configuration file.

## Random/Grid Search Over Parameters

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
