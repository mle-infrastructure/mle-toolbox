# MLE-Toolbox Example Experiments

For all example experiments you can add several command line options:

- `--no_welcome`: Don't print welcome messages at experiment launch.
- `--no_protocol`: Do not record experiment in protocol database.
- `--resource_to_run local`: Run the experiment locally on your machine.


* :page_facing_up: [Experiment Demo on Toy Surrogate](toy_single_objective) - Demo for core toolbox experiment types.

```
mle run toy_single_objective/mle_single_config.yaml         # Run single config experiment
mle run toy_single_objective/mle_multi_config.yaml          # Run multi config experiment
mle run toy_single_objective/mle_search_grid.yaml           # Run async grid search experiment
mle run toy_single_objective/mle_search_smbo.yaml           # Run sync SMBO search experiment
```

* :page_facing_up: [Multi-Objective Search on Toy Surrogate](toy_multi_objective) - Hyperparameter tuning for multi-objective optimization.

```
mle run toy_multi_objective/toy_multi.yaml         # Run Multi-Objective hyperparameter tuning
```

* :page_facing_up: [Bash Multi-Config](bash_multi_config) - Launch multi-configuration experiments for bash based jobs.

```
mle run bash_multi_config/bash_configs.yaml        # Run two configs for 5 seeds each
```

* :page_facing_up: [Quadratic PBT](pbt_quadratic) - Population-Based Training for a quadratic surrogate as in [Jaderberg et al. (2017)](https://arxiv.org/abs/1711.09846).

```
mle run pbt_quadratic/quadratic_pbt.yaml           # Run PBT on `h` params
```
