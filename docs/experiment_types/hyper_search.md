# Hyperparameter Search

Given a fixed training configuration file and the Python training script the only thing that has to be adapted for the different types of experiments is the meta configuration file.

#### Random/grid search over parameters

```yaml
# Meta Arguments: What job? What train .py file?
# Base .json config? Where to store?meta_job_args:
meta_job_args:
    project_name: "ode"
    job_type: "hyperparameter-search"
    base_train_fname: "ode/run_ode_int.py"
    base_train_config: "ode/ode_int_config_1.json"
    experiment_dir: "experiments/"

# Parameters specific to the hyperparameter search
param_search_args:
    search_type: "grid"
    hyperlog_fname: "hyper_log.pkl"
    reload_log: False
    verbose_logging: True
    maximize_objective: True
    problem_type: "final"
    eval_score_type: "integral"
    num_search_batches: 2
    num_iter_per_batch: 5
    num_evals_per_iter: 2
    params_to_search:
        real:
            x_0:
                begin: 1
                end: 10
                bins: 10

# Parameters specific to an individual job
single_job_args:
    job_name: "ode"
    num_gpus: 0
    num_logical_cores: 2
    log_file: "log"
    err_file: "err"
    env_name: "mle-toolbox"
```

#### Sequential model-based optimization

```yaml
# Meta Arguments: What job? What train .py file? Base config? Where to store?
meta_job_args:
    project_name: "ode"
    job_type: "hyperparameter-search"
    base_train_fname: "run_ode_int.py"
    base_train_config: "ode_int_config_1.json"
    experiment_dir: "experiments/smbo/"

# Parameters specific to the hyperparameter search
param_search_args:
    search_type: "smbo"
    hyperlog_fname: "hyper_log.pkl"
    reload_log: False
    verbose_logging: True
    maximize_objective: True
    problem_type: "final"
    eval_score_type: "integral"
    num_search_batches: 3
    num_iter_per_batch: 5
    num_evals_per_iter: 2
    params_to_search:
        real:
            x_0:
                begin: 1
                end: 10
                prior: "log-uniform"    # "uniform", "log-uniform"
    smbo_config:
        base_estimator: "GP"            # "GP", "RF", "ET", "GBRT"
        acq_function: "gp_hedge"        # "LCB", "EI", "PI", "gp_hedge"
        n_initial_points: 10

# Parameters specific to an individual job
single_job_args:
    job_name: "ode"
    num_gpus: 0
    num_logical_cores: 2
    log_file: "log-ode"
    err_file: "error-pde"
    env_name: "multi-agent-cpu"
```
