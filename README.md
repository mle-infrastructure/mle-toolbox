## Lightweight Management of Distributed ML Experiments 🛠️
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-toolbox.svg?style=flat-square)](https://pypi.python.org/pypi/mle-toolbox)
[![Docs Latest](https://img.shields.io/badge/docs-dev-blue.svg)](https://roberttlange.github.io/mle-toolbox/)
[![PyPI version](https://badge.fury.io/py/mle-toolbox.svg)](https://badge.fury.io/py/mle-toolbox)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Status](https://github.com/mle-infrastructure/mle-toolbox/workflows/Python%20tests/badge.svg)](https://github.com/mle-infrastructure/mle-toolbox/actions?query=workflow%3A"Python+tests")
[![codecov](https://codecov.io/gh/mle-infrastructure/mle-toolbox/branch/main/graph/badge.svg?token=0B56UIWGX3)](https://codecov.io/gh/mle-infrastructure/mle-toolbox)

> Coming up with the right hypothesis is hard - testing it should be easy.
<a href="https://roberttlange.github.io/mle-infrastructure/images/logos/toolbox.png"><img src="https://roberttlange.github.io/mle-infrastructure/images/logos/toolbox.png" width="200" align="right" /></a>

ML researchers need to coordinate different types of experiments on separate remote resources. The *Machine Learning Experiment (MLE)-Toolbox* is designed to facilitate the workflow by providing a simple interface, standardized logging, many common ML experiment types (multi-seed/configurations, grid-searches and hyperparameter optimization pipelines). You can run experiments on your local machine, high-performance compute clusters ([Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html)) as well as on cloud VMs ([GCP](https://cloud.google.com/gcp/)). The results are archived (locally/[GCS bucket](https://cloud.google.com/products/storage/)) and can easily be retrieved or automatically summarized/reported.

![](https://github.com/mle-infrastructure/mle-toolbox/blob/main/docs/mle_run.gif?raw=true)

## What Does The `mle-toolbox` Provide?

1. API for launching jobs on cluster/cloud computing platforms (Slurm, GridEngine, GCP).
2. Common machine learning research experiment setups:
    - Launching and collecting multiple random seeds in parallel/batches or async.
    - Hyperparameter searches: Random, Grid, SMBO, PBT and Nevergrad.
    - Pre- and post-processing pipelines for data preparation/result visualization.
3. Automated report generation for hyperparameter search experiments.
4. Storage of results and database in Google Cloud Storage Bucket.
5. Resource monitoring with dashboard visualization.

![](https://github.com/mle-infrastructure/mle-toolbox/blob/main/docs/mle_toolbox_structure.png?raw=true)

## The 4 Step `mle-toolbox` Cooking Recipe 🍲

1. Follow the [instructions below](https://github.com/mle-infrastructure/mle-toolbox#installation-) to install the `mle-toolbox` and set up your credentials/configurations.
2. Read the [docs](https://mle-infrastructure.github.io/mle-toolbox) explaining the pillars of the toolbox & the experiment meta-configuration job `.yaml` files .
3. Check out the [examples 📄](https://github.com/mle-infrastructure/mle-toolbox#examples-school_satchel) to get started: Toy [ODE integration](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/numpy_pde), training [PyTorch MNIST-CNNs](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/torch_mnist) or [VAEs in JAX](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/jax_vae).
4. Run your own experiments using the [template files, project](https://github.com/mle-infrastructure/mle-project) and [`mle run`](https://roberttlange.github.io/mle-infrastructure/core_api/mle_run/).


## Installation ⏳

If you want to use the toolbox on your local machine follow the instructions locally. Otherwise do so on your respective cluster resource (Slurm/SGE). A PyPI installation is available via:

```
pip install mle-toolbox
```

Alternatively, you can clone this repository and afterwards 'manually' install it:

```
git clone https://github.com/mle-infrastructure/mle-toolbox.git
cd mle-toolbox
pip install -e .
```

By default this will only install the minimal dependencies (not including specialized packages such as `scikit-optimize`, `statsmodels`, `nevergrad` etc.). To get all requirements for tests or examples you will need to install [additional requirements](requirements/).


#### Setting Up Your Remote Credentials 🙈

By default the toolbox will only run locally and without any GCS storage of your experiments. If you want to integrate the `mle-toolbox` with your SGE/Slurm clusters, you have to provide additional data. There 2 ways to do so:

1. After installation type `mle init`. This will walk you through all configuration steps in your CLI and save your configuration in `~/mle_config.toml`.
2. Manually edit the [`config_template.toml`](config_template.toml) template. Move/rename the template to your home directory via `mv config_template.toml ~/mle_config.toml`.

The configuration procedure consists of 3 optional steps, which depend on your needs:

1. Set whether to store all results & your database locally or remote in a GCS bucket.
2. Add SGE and/or Slurm credentials & cluster-specific details (headnode, partitions, proxy server, etc.).
3. Add the GCP project, GCS bucket name and database filename to store your results.


## The Core Commands of the MLE-Toolbox 🌱

You are now ready to dive deeper into the specifics of [job configuration](https://roberttlange.github.io/mle-infrastructure) and can start running your first experiments from the cluster (or locally on your machine) with the following commands:

|   | Command              |        Description                                                        |
|-----------| -------------------------- | -------------------------------------------------------------- |
|⏳| [`mle init`](https://roberttlange.github.io/mle-infrastructure/core_api/mle_init/)       | Setup of credentials & toolbox settings.              |
|🚀| [`mle run`](https://roberttlange.github.io/mle-infrastructure/core_api/mle_run/)       | Start up an experiment.              |
|🖥️| [`mle monitor`](https://roberttlange.github.io/mle-infrastructure/core_api/mle_monitor/)       | Monitor resource utilisation.              |
|📥	| [`mle retrieve`](https://roberttlange.github.io/mle-infrastructure/core_api/mle_retrieve/)       | Retrieve an experiment result.              |
|💌| [`mle report`](https://roberttlange.github.io/mle-infrastructure/core_api/mle_report/)       | Create an experiment report with figures.              |
|🔄| [`mle sync-gcs`](https://roberttlange.github.io/mle-infrastructure/core_api/mle_sync_gcs/)       | Extract all GCS-stored results to your local drive.              |
|🔄| `mle project`    | Initialize a new project by cloning [`mle-project`](https://github.com/mle-infrastructure/mle-project).   
|📝| `mle protocol`    | List a summary of the most recent experiments.

## Examples 🎒

|              | Job Types|        Description                                                        |
| -------------------------- |-------------- | -------------------------------------------------------------- |
| 📄 **[Single-Objective](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/toy_single_objective)** |  `multi-configs`, `hyperparameter-search`     | Core experiment types.              |
| 📄 **[Multi-Objective](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/toy_multi_objective)**       | `hyperparameter-search`     | Multi-objective tuning. |
|  📄 **[Multi Bash](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/bash_multi_config)**      | `multi-configs`     | Bash-based jobs.                        |
| 📄 **[Quadratic PBT](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/pbt_quadratic)**            | `population-based-training`    | PBT on toy quadratic surrogate.                          |
| 📓 **[Evaluation](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/evaluate_results.ipynb)**          | -     | Evaluation of gridsearch results. |
| 📓 **[GIF Animations](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/animate_results.ipynb)** | -     | Walk through a set of animation helpers.      |
| 📓 **[Testing](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/hypothesis_testing.ipynb)**     | -     | Perform hypothesis tests on logs.        |
|📓 **[PBT Evaluation](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/inspect_pbt.ipynb)** | -     | Inspect the result from PBT.                                   |

### Acknowledgements & Citing `mle-toolbox` ✏️

To cite this repository:

```
@software{mle_infrastructure2021github,
  author = {Robert Tjarko Lange},
  title = {{MLE-Infrastructure}: A Set of Lightweight Tools for Distributed Machine Learning Experimentation},
  url = {http://github.com/mle-infrastructure},
  version = {0.3.0},
  year = {2021},
}
```

Much of the `mle-toolbox` design has been inspired by discussions with [Jonathan Frankle](http://www.jfrankle.com/) and [Nandan Rao](https://twitter.com/nandanrao) about the quest for empirically sound and supported claims in Machine Learning. Finally, parts of the `mle <subcommands>` were inspired by Tudor Berariu's [Liftoff package](https://github.com/tudor-berariu/liftoff) and parts of the philosophy by wanting to provide a light-weight version of IDISA's [sacred package](https://github.com/IDSIA/sacred). Further credit goes to [Facebook's `submitit`](https://github.com/facebookincubator/submitit) and [Ray](https://github.com/ray-project/ray).

## Notes, Development & Questions ❓

- If you find a bug or want a new feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue 🤗
- You can check out the history of release modifications in [`CHANGELOG.md`](https://github.com/RobertTLange/mle-toolbox/blob/main/CHANGELOG.md) (*added, changed, fixed*).
- You can find a set of open milestones in [`CONTRIBUTING.md`](https://github.com/RobertTLange/mle-toolbox/blob/main/CONTRIBUTING.md).
