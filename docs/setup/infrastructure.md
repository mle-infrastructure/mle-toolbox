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
"train_config": {"x_0": 100,
                 "t_max": 1000,
                 "dt": 0.1,
                 "log_every_steps": 1000},
# Net construction configuration: Layer info (if there was a net to train)
"net_config": {},
# Logging configuration: What to log/print & tensorboard file name
"log_config": {"time_to_track": ["step_counter"],
               "what_to_track": ["integral"],
               "tboard_fname": "ode_fun",
               "time_to_print": ["step_counter"],
               "what_to_print": ["integral"],
               "print_every_k_updates": 10,
               "overwrite_experiment_dir": 0}
}

```

### The `.py` training script

```Python
import numpy as np
# Import the command line input processor & the experiment logger
from mle_toolbox.utils import get_configs_ready, DeepLogger

def main(train_config, net_config, log_config):
    """ Euler integrate a simple ODE. """
    # Instantiate the logger object for the experiment
    log = DeepLogger(**log_config)

    # Define function to integrate & run the integration
    def func(x):
        return -0.1*x

    x_t = [train_config.x_0 + train_config.seed_id]
    t_seq = np.arange(train_config.dt, train_config.t_max,
                      train_config.dt).tolist()

    for i, t in enumerate(t_seq):
        # Perform the one-step Euler update
        x_t.append(x_t[-1] + func(x_t[-1])*train_config.dt)

        # Update & save the newest log
        if (i % train_config.log_every_steps) == 0:
            time_tick = [i+1]
            stats_tick = [x_t[-1]]
            log.update_log(time_tick, stats_tick)
            log.save_log()
    return

if __name__ == "__main__":
    # Load in the configuration for the experiment & unpack
    configs = get_configs_ready(default_config_fname="ode_int_config_1.json")
    train_config, net_config, log_config = configs
    # Run the simulation/Experiment
    main(train_config, net_config, log_config)
```
