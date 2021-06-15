# Toolbox Infrastructure

In this document you can learn everything about how to run experiments with the `mle-toolbox`. The `mle-toolbox` allows you to run different types of experiments locally or on an SGE cluster. You have to provide three inputs:

1. An experiment/meta configuration `.yaml` file.
2. A job configuration `.json`file.
3. A python `.py` script that runs your training loop.

<a href="toolbox-schematic.png"><img src="toolbox-schematic.png" width=900 align="center" /></a>


## Running an `mle-toolbox` experiment

The only things you have to do is specify your desired experiment protocol.

It automatically detects whether you start an experiment with access to multiple compute nodes.

- `train.py` takes three arguments: `-config`, `-seed`, `-exp_dir`
- This includes the standard inputs to the training function (`net_config`, `train_config`, `log_config`) but can be otherwise generalised to your applications.

<a href="toolbox-inputs.png"><img src="toolbox-inputs.png" width=900 align="center" /></a>

### The `.yaml` experiment configuration file

```yaml
# Meta Arguments: What job? What train .py file?
# Base .json config? Where to store?
meta_job_args:
    project_name: "ode"
    job_type: "multiple-experiments"
    base_train_fname: "ode/run_ode_int.py"
    experiment_dir: "experiments/"

# Parallel experiments: Over 2 configs & 10 seeds
multi_experiment_args:
    config_fnames:
        - "ode/ode_int_config_1.json"
        - "ode/ode_int_config_2.json"
    num_seeds: 10

# Parameters for individual job: 2 logical cores
single_job_args:
    job_name: "ode"
    num_logical_cores: 2
    log_file: "l-ode"
    err_file: "e-ode"
    env_name: "mle-toolbox"

```

### The `.json` training configuration file

```json
{
# Training configuration: Adapted by hyperparameter search
"train_config": {"learning_rate": 3e-04,
                 "num_steps": 1000,
                 "log_every_steps": 10},
# Net construction configuration: Layer info (if there was a net to train)
"net_config": {},
# Logging configuration: What to log/print & tensorboard file name
"log_config": {"time_to_track": ["timestamp1"],
               "what_to_track": ["metric1"],
               "tboard_fname": "tb",
               "time_to_print": ["timestamp1"],
               "what_to_print": ["metric1"],
               "print_every_k_updates": 10,
               "overwrite_experiment_dir": 1}
}

```

### The `.py` training script

```Python
# Import MLE wrapper processing cmd inputs and logging
from mle_toolbox import MLExperiment

def main(mle):
    """ Main Training Loop Function. """
    # Setup your experiment - e.g. build a network with `mle.net_config`
    for t in range(mle.train_config.num_steps):
        # Perform the one-step optimization update
        ...
        # Update & save the newest log
        if (i % train_config.log_every_steps) == 0:
            time_tick = {"timestamp1": t+1}
            stats_tick = {"metrix": t*mle.train_config.learning_rate}
            log.update_log(time_tick, stats_tick, save=True)
    return

if __name__ == "__main__":
    # Load in config for the experiment & run the simulation
    mle = MLExperiment()
    main(mle)
```
