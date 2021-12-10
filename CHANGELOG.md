### v0.3.2 - TBD

##### Added

##### Changed

##### Fixed


### v0.3.2 - 12/10/2021

##### Added

- Introduces experimental notebook-friendly `MLELauncher` which allows you to schedule experiments from within a local notebook.
- Adds `mle protocol` subcommand to get a quick view of the last experiments and their status.
- Adds `mle project` to initialize a new project based on cloning the [`mle-project`](https://github.com/mle-infrastructure/mle-project) repository.

##### Changed

- Refactors out resource monitoring and protocol database to `mle-monitor` sub-package.
- Refactors out job launching and status monitoring to `mle-launcher` sub-package.
- Moves population-based training and hypothesis testing into `experimental` submodule.
- Moves documentation page to `mle-docs` sub-repository.


### v0.3.1 - 10/20/2021

##### Added

- 3D animation post-processing helpers (`animate_3D_scatter` and `animate_3D_surface`) and test coverage for visualizations (static/dynamic).
- [`nevergrad`](https://facebookresearch.github.io/nevergrad/index.html) multi-objective hyperparameter optimization. Checkout the toy [example](examples/toy_multiobj).
- Adds `@experiment` decorator for easy integration:

```python
from mle_toolbox import experiment

@experiment("configs/abc.json", model_config={"num_layers": 2})
def run(mle, a):
    print(mle.model_config)
    print(mle.log)
    print(a)

if __name__ == "__main__":
  run(a=2)
```

- Adds `combine_experiments` which loads different `meta_log` and `hyper_log` objects and makes them "dot"-accessible:
```python
experiment_dirs = ["../tests/unit/fixtures/experiment_1",
                   "../tests/unit/fixtures/experiment_2"]
meta, hyper = combine_experiments(experiment_dirs, aggregate_seeds=False)
```

- Adds option to run grid search for multiple base configurations without having to create individual experiment configuration files.

##### Changed

- Configuration loading is now more toolbox specific. `load_json_config` and `load_yaml_config` are now part of `mle-logging`. The toolbox now has two "new" function `load_job_config` and `load_experiment_config`, which prepare the raw configs for future usage.
- The `job_config` file now no longer has to be a `.json` file, but can (and probably should) be a `.yaml` file. This makes formatting easier. The hyperoptimization pipeline will generate configuration files that are of the same file type.
- Moves core hyperparameter optimization functionality to [`mle-hyperopt`](https://github.com/RobertTLange/mle-hyperopt). At this point the toolbox wraps around the search strategies and handles the `mle-logging` log loading/data retrieval.
- Reduces test suite since all hyperopt strategy-internal tests are taken care of in `mle-hyperopt`.

##### Fixed

- Fixed unique file naming of zip files stored in GCS bucket. Now based on the time string.
- Grid engine monitoring now also tracks waiting/pending jobs.
- Fixes a bug in the random seed setting for synchronous batch jobs. Previously a new set of seeds was sampled for each batch. This lead to problems when aggregating different logs by their seed id. Now the first set of seeds is stored and provided as an input to all subsequent `JobQueue` startups.

### v0.3.0 - 08/21/2021

##### Added
- Adds general processing job, which generalizes the post-processing job and enables 'shared'/centralized data pre-processing before a (search) experiment and results post-processing/figure generation afterwards. Checkout the [MNIST example](https://github.com/RobertTLange/mle-toolbox/blob/main/examples/torch_mnist/mnist_single.yaml).
- Adds population-based training experiment type (still experimental). Checkout the [MNIST example](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/pbt_mnist) and the [simple quadratic from the paper](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/pbt_quadratic).
- Adds a set of unit/integration tests for more robustness and `flake8` linting.
- Adds code coverage with secrets token.
- Adds `mle.ready_to_log` based on `log_every_k_updates` in `log_config`. No more modulo confusion.
- Adds [slack clusterbot integration](https://github.com/sprekelerlab/slack-clusterbot/) which allows for notifications and report upload.

##### Changed
- Allow logging of array data in meta log `.hdf5` file by making `tolerant_mean` work for matrices.
- Change configuration .yaml to use `experiment_type` instead of `job_type` for clear distinction:
  - *job*: Single submission process on resource (e.g. single seed for single configuration)
  - *eval*: Single parameter configuration which can be executed/trained for multiple seeds (individual jobs!)
  - *experiment*: Refers to entire sequence of jobs to be executed (e.g. grid search with pre/post-processing)
- Restructure `experiment` subdirectory into `job` for consistent naming.
- Refactor out `MLELogger` into separate `mle-logging` package. It is a core ingredient that should stand alone.

##### Fixed

- Fixed `mle retrieve` to be actually useful and work robustly.
- Fixed `mle report` to retrieve results if they don't exist (or to use a local directory provided by the user).
- Fixed `mle report` to generate reports via `.html` file and the dependency `xhtml2pdf`.
- Fixed unique hash for experiment results storage. Previously this only used the content of `base_config.json`, which did not result in a unique hash when running different searches via `job_config.yaml`. Now the hash is generated based on a merged dictionary of the time string, `base_config` and `job_config`

### v0.2.9 - 06/23/2021

##### Added

- Adds monitoring panel for GCP in `mle monitor` dashboard.
- Adds asynchronous job launching via new `ExperimentQueue` and monitoring based on `max_running_jobs` budget. This release changes the previous job launching infrastructure. We no longer rely on one process per job, but monitor all scheduled jobs passively in a for-loop.
- Adds GitHub Pages hosted documentation using mkdocs and the Material framework. The documentation is hosted under roberttlange.github.io/mle-toolbox. It is still very much work in progress.

##### Changed

- Adds support for additional setup bash files when launching GCP VM in `single_job_args`.
- Adds Q/A for upload/deletion of directory to GCS bucket.
- All GCP-CPU resources are now queried via [custom machine types](https://cloud.google.com/compute/docs/instances/creating-instance-with-custom-machine-type#gcloud) - Default cheap n1.
- Separate different `requirements.txt` for minimal installation, examples and testing.
- Restructures the search experiment API in the `.yaml` file. We now differentiate between 3 pillars:
    1. `search_logging`: General options such as reloading of previous log, verbosity, metrics in `.hdf5` log to monitor and how to do so.
    2. `search_resources`: How many jobs, batches, maximum number of simultaneously running jobs, etc..
    3. `search_config`: Options regarding the search type (random, grid, smbo) and the parameters to search over (spaces, resolution, etc.).


### v0.2.8 - 05/06/2021

##### Added

- Adds `HypothesisTester`: Simple time average difference comparison between individual runs. With multiple testing correction and p-value plotting. Example `hypothesis_testing.ipynb` notebook.
- Adds `MetaLog` and `HyperLog` classes: Implement convenient functionalities like `hyper_log.filter()` and ease the post-processing analysis.
- Adds GCP job launch/monitor support for all experiment types and organizes GCS syncing of results.

##### Changed

- `load_result_logs` is now directly imported with `import mle_toolbox` since it is part of the core functionality.
- Major restructuring of `experiment` sub-directory (`local`, `cluster`, `cloud`) with easy 3 part extension for new resources:
    1. `monitor`
    2. `launch`
    3. `check_job_args`

##### Fixed

- Fixes plotting with new `MetaLog` and `HyperLog` classes.

### v0.2.7 - 04/24/2021

##### Added
- Allows multi-config + multi-seed bash experiments. The user needs to take care of the input arguments (`-exp_dir`, `-config_fname`, `-seed_id`) themselves and within the bash script. We provide a minimal example of how to do so in examples/bash_configs.
- Adds backend functions for `monitor_slurm_cluster` and local version to get resource utilisation.
- Adds SHA-256 encryption/decryption of ssh credentials. Also part of initialization setup.
- Adds `extra_cmd_line_inputs` to `single_job_args` so that you can add a static input via the command line. This will also be incorporated in the `MLExperiment` as `extra_config` `dotmap` dictionary.

##### Changed
- Changes plots of monitored resource utilisation to `plotext` to avoid gnuplot dependency.
- Changes logger interface: Now one has to provide dictionaries as inputs to `update_log`. This is supposed to make the logging more robust.
- Changes template files and refactor/name files in `utils` subdirectory:
    - `core_experiment`: Includes helpers used in (almost) every experiment
    - `core_files_load`: Helpers used to load various core components (configs)
    - `core_files_merge`: Helpers used to merge meta-logs
    - `helpers`: Random small functionalities (not crucial)
- Renames `hyperopt` subdirectory: `hyperopt_<type>`, `hyperspace`, `hyperlogger`
- Changes the naming of the config from `cc` to `mle_config` for easy readability.
- Changes the naming of files to be more intuitive: E.g. `abc_1_def.py`, `abc_2_def.py` are changed to `abc_def_1.py`, `abc_def_2.py`

##### Fixed
- Fixed local launch of remote projects via `screen` session and pipping to `qrsh` or `srun --pty bash`. If you are on a local machine and run `mle run`, you will get to choose the remote resource and can later reattach to that resource.
- Fixed 2D plot with `fixed_params`. The naming as well as subtitle of the `.png` files/plots accounts for the fixed parameter.


### v0.2.6 - 04/09/2021
- Adds `mle init` to configure template toml. The command first searches for an existing config to update. If none is found we go through the process of updating values in a default config.
- Print configuration and protocol summary with rich. This gets rid of `tabulate` dependency.
- Update `monitor_slurm_cluster` to work with new `mle monitor`. This gets rid of `colorclass`, `terminaltables` dependencies.
- Fix report generation bug (everything has to be a string for markdown-ification!).
- Fix monitor bug: No longer reload the local database at each update call.
- Adds `get_jax_os_ready` helper for setting up JAX environment variables.
- Adds `load_model_ckpt` for smooth reloading of stored checkpoints.
- Add `MLE_Experiment` abstraction for minimal imports and smooth workflow.
- A lot of internal refactoring: E.g. getting rid of `multi_runner` sub directory.


### v0.2.5 - 04/05/2021
- Raw github links for figures in readme so they are rendered in PyPi.
- Introduce mle-config variable `use_conda_virtual_env` to allow user to choose between `conda` and `venv` virtual environment setup.
- Introduce mle-config variable `remote_env_name` to allow user to set name for the remote experiment execution environment.
- Fix GCS retrieval unzipping so that there are no redundant sub-directories
- Make logging even better (different model types and top-k checkpointing)
- Add sklearn SVM classifier + Haiku VAE example with .pkl model saving
- Add rich dashboard for `monitor-cluster` :heart: (running only on SGE grid for now)
- Major clean-up of `utils`. Rename things properly e.g.`hyper_log_to_df` -> `load_hyper_log` and add top-k selection next to variable fixing in `subselect_hyper_log`
- Refactoring of core src commands and rebranding of core cmd line interface. You now call mle-toolbox commands via `mle <subcmd> <options>`. The toolbox has the following subcommands:
    - `run`: Run a new experiment on a resource available to you.
    - `retrieve`: Retrieve a completed experiment from a cluster/GCS bucket.
    - `report`: Generate a set of reports (.html/.md) from experiment results.
    - `monitor`: Monitor a compute resource and view experiment protocol.
    - `sync-gcs`: Sync all results from Google Cloud Storage


### v0.2.4 -02/16/2021
- Major reduction of dependencies. Now for all more optional/specialized features (e.g. SMBO, visualization, JAX/torch idiosyncracies) there will be an exception raised if the package isn't installed and you still want to use the toolbox feature.
- Refactored `visualization` into its own subdirectory to clean up `utils`.
- Change from own `DotDic` to `DotMap`, which appears more stable and better maintained. Be aware that now we can't rely on `None` outputs if key is not in dict. We shouldn't have done that in the first place due to being error prone.
- Got rid of `cross_validation` support. This made everything less clean/minimal and can be handled within your specific setup.
- Now we also store much more meta data in the `hyper_log.pkl` file output from the search. This includes potential checkpoint paths of networks, multiple target variables and the original log paths.
- Added the `report-experiment` core functionality to generate `.md`, `.html` and `.pdf` reports of your experiments.
- Added an example notebook that shows how to load/analyze and report the results from the simple ODE integration example.


### v0.2.3 - 02/16/2021
- Minor update to the credential `.toml` template file
