# Project Template

In order to get a feeling for how an experiment based on the toolbox utilities may look like, checkout the [project template repository](https://github.com/RobertTLange/mle-project-template).

## General Directory Structure

```
mle-project-template
├── configs: Training configurations (base and cluster searches)
    ├── train: .json training configuration
    ├── cluster: .yaml experiment configuration
├── docs: Some work-in-progress notes/documentation
├── experiments: Main directory storing results
├── notebooks: Sanity checks & result visualization
    ├── 01_viz_results.ipynb: Visualize some results
├── utils: Helper functions (data generation, networks, training helpers)
├── cluster_exec.sh: Main training loop
├── mle_bash.sh: Main training loop as bash program
├── mle_python.py: Main training loop as python program
├── Readme.md: Documentation
├── requirements.txt: Dependencies
```

### `.yaml` experiment configuration

The `.yaml` file specifies what type of experiment you want to run. It consists of two core ingredients (`meta_job_args` and `single_job_args`) which have to be provided with every experiment type:

```yaml
# Meta Arguments: What job? What train .py file?
# Base .json config? Where to store?
meta_job_args:
    # Choose a project name used for logging your experiments
    project_name: "<project_name>"
    # Specifies what experiment to run. Can be one of the following:
    # 'single-config', 'multiple-configs', 'hyperparameter-search',
    # 'population-based-training'
    experiment_type: "<experiment_type>"
    base_train_fname: "mle_python.py"
    base_train_config: "train/<base_config>.json"
    experiment_dir: "experiments/"

# Parameters for individual job: 2 logical cores
single_job_args:
    job_name: "ode"
    num_logical_cores: 2
    log_file: "log"
    err_file: "err"
    env_name: "mle-toolbox"
```

They provide the most general information required to launch a single job that will execute `mle_python.py` on a resource with two logical cores. Additionally and depending on the settings you want to run please provide one of the following additional ingredients:

- [Pre/Post-Processing](../../experiment_types/single_pre_post/): `pre_processing_args` and/or `post_processing_args`
- [Multiple Configurations](../../experiment_types/multiple_configs/): `multi_config_args`
- [Grid/Random Search/SMBO](../../experiment_types/hyperparameter_search/): `param_search_args`
- [Population-Based Training](../../experiment_types/population_based_training/): `pbt_args`

### `.json` training configuration

The `.json` file, on the other hand, specifies the `train_config`, `log_config` and (optionally) `model_config`, which are provided to a job. They can be easily accessed via the `MLExperiment` class instance (see below):

```json
{
# Training configuration: Adapted by hyperparameter search
"train_config": {"learning_rate": 3e-04,
                 ...},
# Model configuration: Layer info (if there was a net to train)
"model_config": {"num_hidden_layers": 2,
                 ...},
# Logging configuration: What to log/print & tensorboard file name
"log_config": {"time_to_track": ["timestamp1"],          # Var names of timestamps
               "what_to_track": ["metric1", "metric2"],  # Var names of stats vars
               "time_to_print": ["timestamp1"],          # Time var names to print
               "what_to_print": ["metric1"],             # Stats var names to print
               "print_every_k_updates": 1,               # How often to print
               "overwrite_experiment_dir": 1}            # Whether to overwrite existing dir
}
```

Importantly, when launching a grid search experiment the toolbox will copy the base configuration file and modify the variables in `train_config` which you intend to search over.

### `.py` training script file

```Python
# Import MLE wrapper processing cmd inputs and logging
from mle_toolbox import MLExperiment

def main(mle):
    """ Main Training Loop Function. """
    # Setup your experiment - e.g. build a network with `mle.model_config`
    model = build_model(**mle.model_config)

    # Run the main training loop
    for t in range(mle.train_config.num_steps):
        # Perform the one-step optimization update
        metric1, metric2 = ...
        # Update & save the newest log
        if (i % mle.train_config.log_every_steps) == 0:
            time_tick = {"timestamp1": t+1}
            stats_tick = {"metric1": metric1,
                          "metric2": metric2}
            # Store results
            mle.log.update_log(time_tick, stats_tick, save=True)
    return

if __name__ == "__main__":
    # Load in config for the experiment & run the simulation
    mle = MLExperiment()
    main(mle)
```

### `.sh` training script file

You can also launch experiments which are not Python-based. In that case you cannot rely on the `.hdf5` logging utilities or the `hyper_log.pkl` aggregation of search experiments. But this is not a problem as long as you set the `no_results_logging` boolean in the `param_search_args["search_logging"]` `.yaml` configuration.

```bash
#!/bin/sh
# GET_CONFIGS_READY FOR BASH FILE!
POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

# Define commandline processing of arguments
case $key in
    -exp_dir|--experiment_dir)
    EXPERIMENT_DIR="$2"
    shift # past argument
    shift # past value
    ;;
    -config|--config_fname)
    CONFIG_FNAME="$2"
    shift # past argument
    shift # past value
    ;;
    -seed|--seed_id)
    SEED_ID="$2"
    shift # past argument
    shift # past value
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

for i in $(seq 0 ${IMP_ITERS})
do
  python main.py --config_fname ${CONFIG_FNAME}  --seed_id ${SEED_ID} \
      --experiment_dir ${EXPERIMENT_DIR}
done
```
