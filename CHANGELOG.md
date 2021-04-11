**TODO**:
- Add backend functions for `monitor_slurm_cluster` and local version
- Make `mle init` beautiful/a smoother experience.
- Make bash experiments with inputs possible.
- Smoothly launch remote jobs from local machine.
- Asynchronous job scheduling based on "trigger event"
- Population-based training.


**v0.2.7**
- Changes plots of monitored resource utilisation to `plotext` to avoid gnuplot dependency.
- Change logger interface: Now one has to provide dictionaries as inputs to `update_log`. This is supposed to make the logging more robust.
- Update template files and refactor/name files in `utils` subdirectory:
    - `core_experiment`: Includes helpers used in (almost) every experiment
    - `core_files_load`: Helpers used to load various core components (configs)
    - `core_files_merge`: Helpers used to merge meta-logs
    - `helpers`: Random small functionalities (not crucial)


**v0.2.6**
- Adds `mle init` to configure template toml. The command first searches for an existing config to update. If none is found we go through the process of updating values in a default config.
- Print configuration and protocol summary with rich. This gets rid of `tabulate` dependency.
- Update `monitor_slurm_cluster` to work with new `mle monitor`. This gets rid of `colorclass`, `terminaltables` dependencies.
- Fix report generation bug (everything has to be a string for markdown-ification!).
- Fix monitor bug: No longer reload the local database at each update call.
- Adds `get_jax_os_ready` helper for setting up JAX environment variables.
- Adds `load_model_ckpt` for smooth reloading of stored checkpoints.
- Add `MLE_Experiment` abstraction for minimal imports and smooth workflow.
- A lot of internal refactoring: E.g. getting rid of `multi_runner` sub directory.


**v0.2.5**
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


**v0.2.4**
- Major reduction of dependencies. Now for all more optional/specialized features (e.g. SMBO, visualization, JAX/torch idiosyncracies) there will be an exception raised if the package isn't installed and you still want to use the toolbox feature.
- Refactored `visualization` into its own subdirectory to clean up `utils`.
- Change from own `DotDic` to `DotMap`, which appears more stable and better maintained. Be aware that now we can't rely on `None` outputs if key is not in dict. We shouldn't have done that in the first place due to being error prone.
- Got rid of `cross_validation` support. This made everything less clean/minimal and can be handled within your specific setup.
- Now we also store much more meta data in the `hyper_log.pkl` file output from the search. This includes potential checkpoint paths of networks, multiple target variables and the original log paths.
- Added the `report-experiment` core functionality to generate `.md`, `.html` and `.pdf` reports of your experiments.
- Added an example notebook that shows how to load/analyze and report the results from the simple ODE integration example.


**v0.2.2**
- Minor update to the credential `.toml` template file
