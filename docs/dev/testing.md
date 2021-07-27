# Running The Test Suite

## `flake8` Linting

```
flake8 ./mle_toolbox --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 ./mle_toolbox --count --exit-zero --max-line-length=127 --statistics
```

## `mypy` Type Checking

```
mypy mle_toolbox/.
```

## `black` Formatting

```
black mle_toolbox/. --verbose
```

## Test Coverage

*Note*: This page and content is still work in progress!

### Unit Tests

```
pytest -vv tests/unit
```

- [ ] File loading: `tests/unit/test_load_files.py`
    - [x] `.yaml` experiment configuration
    - [x] `.json` run configuration
    - [x] `meta_log.hdf5`
    - [x] `hyper_log.pkl`
    - [ ] Trained models
        - [ ] `.pkl`-based (sklearn)
        - [ ] `.npy`-based (JAX)
        - [ ] `.pt`-based (PyTorch)

- [ ] Experiment launch configuration file generation
    - [ ] `.qsub`
    - [ ] `.sbash`
    - [ ] GCP-startup `.sh` file

- [ ] Logging
    - [ ] Individual run
        - [ ] assert key errors
        - [ ] directory creation - correct file structure
        - [ ] are files stored in correct location?
        - [ ] is data correctly stored?
    - [ ] Merging into `meta_log.hdf5`
    - [ ] Summary into `hyper_log.pkl`
    - [ ] Reloading correctly
    - [ ] All data types supported
    - [ ] Tensorboard support
    - [ ] Image storage support

- [ ] Experiment Protocol Logging
    - [ ] Adding a new experiment
    - [ ] Deleting a failed experiment

### Integration Tests

```
pytest -vv tests/integration
```

- [ ] Experiment types running on different resources
    - [x] Single configuration experiment: `tests/integration/test_single_config.py`
    - [ ] Random search experiment
    - [ ] Grid search experiment
    - [ ] SMBO search experiment
    - [ ] PBT experiment

- [ ] Report generation
    - [ ] Figure generation from meta-log
    - [ ] Figure generation from hyper-log
    - [ ] .md generation

- [ ] Results retrieval
    - [ ] From GCS bucket
    - [ ] From remote resource

- [ ] Toolbox initialization
    - [ ] Config file changing
    - [ ] Encryption ssh credentials

- [ ] GCS integration
