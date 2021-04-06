**v0.2.6**
- Add `mle init` to configure template toml. The command first searches for an existing config to update. If none is found we go through the process of updating values in a default config.
- Print configuration and protocol summary with rich. This gets rid of `tabulate` dependency.
- Update `monitor_slurm_cluster` to work with new `mle monitor`. This gets rid of `colorclass`, `terminaltables` dependencies.


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
