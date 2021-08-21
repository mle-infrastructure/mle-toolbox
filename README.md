![MLE_Toolbox_Banner](https://roberttlange.github.io/mle-toolbox/thumbnails/mle_thumbnail.png)
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-toolbox.svg?style=flat-square)](https://pypi.python.org/pypi/mle-toolbox)
[![Docs Latest](https://img.shields.io/badge/docs-dev-blue.svg)](https://roberttlange.github.io/mle-toolbox/)
[![PyPI version](https://badge.fury.io/py/mle-toolbox.svg)](https://badge.fury.io/py/mle-toolbox)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Status](https://github.com/RobertTLange/mle-toolbox/workflows/Python%20tests/badge.svg)](https://github.com/RobertTLange/mle-toolbox/actions?query=workflow%3A"Python+tests")
[![codecov](https://codecov.io/gh/RobertTLange/mle-toolbox/branch/main/graph/badge.svg?token=0B56UIWGX3)](https://codecov.io/gh/RobertTLange/mle-toolbox)

> Coming up with the right research hypotheses is hard - testing them should be easy.

ML researchers need to coordinate different types of experiments on separate remote resources. The *Machine Learning Experiment (MLE)-Toolbox* is designed to facilitate the workflow by providing a simple interface, standardized logging, many common ML experiment types (multi-seed/configurations, grid-searches and hyperparameter optimization pipelines). You can run experiments on your local machine, high-performance compute clusters ([Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html)) as well as on cloud VMs ([GCP](https://cloud.google.com/gcp/)). The results are archived (locally/[GCS bucket](https://cloud.google.com/products/storage/)) and can easily be retrieved or automatically summarized/reported as `.md`/`.html` files.

## What Does The `mle-toolbox` Provide?

1. API for launching jobs on cluster/cloud computing platforms (Slurm, GridEngine, GCP).
2. Common machine learning research experiment setups:
    - Launching and collecting multiple random seeds in parallel/batches.
    - Hyperparameter searches: Random, Grid, SMBO, Population-Based Training.
    - Pre- and post-processing pipelines for data preparation/result visualization.
3. Automated report generation for hyperparameter searches.
4. Storage of results and database in Google Cloud Storage Bucket.
5. Resource monitoring with dashboard visualization.


## The 4 Step `mle-toolbox` Cooking Recipe 🍲

1. Follow the [instructions below](https://github.com/RobertTLange/mle-toolbox#installation-memo) to install the `mle-toolbox` and set up your credentials/configurations.
2. Read the [docs](https://roberttlange.github.io/mle-toolbox) explaining the pillars of the toolbox & the experiment meta-configuration job `.yaml` files .
3. Check out the [examples 📄](https://github.com/RobertTLange/mle-toolbox#examples-school_satchel) to get started: Toy [ODE integration](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/numpy_ode), training [PyTorch MNIST-CNNs](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/torch_mnist) or [VAEs in JAX](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/jax_vae).
4. Run your own experiments using the [template files, project](https://github.com/RobertTLange/mle-project-template) and [`mle run`](https://roberttlange.github.io/mle-toolbox/core_api/mle_run/).


## Installation ⏳

If you want to use the toolbox on your local machine follow the instructions locally. Otherwise do so on your respective cluster resource (Slurm/SGE). A PyPI installation is available via:

```
pip install mle-toolbox
```

Alternatively, you can clone this repository and afterwards 'manually' install it:

```
git clone https://github.com/RobertTLange/mle-toolbox.git
cd mle-toolbox
pip install -e .
```

By default this will only install the minimal dependencies (not including specialized packages such as `scikit-optimize`, `statsmodels`, etc.). To get all requirements for tests or examples you will need to install [additional requirements](requirements/).


#### Setting Up Your Remote Credentials 🙈

By default the toolbox will only run locally and without any GCS storage of your experiments. If you want to integrate the `mle-toolbox` with your SGE/Slurm clusters, you have to provide additional data. There 2 ways to do so:

1. After installation type `mle init`. This will walk you through all configuration steps in your CLI and save your configuration in `~/mle_config.toml`.
2. Manually edit the [`config_template.toml`](config_template.toml) template. Move/rename the template to your home directory via `mv config_template.toml ~/mle_config.toml`.

The configuration procedure consists of 3 optional steps, which depend on your needs:

1. Set whether to store all results & your database locally or remote in a GCS bucket.
2. Add SGE and/or Slurm credentials & cluster-specific details (headnode, partitions, proxy server, etc.).
3. Add the GCP project, GCS bucket name and database filename to store your results.


## The Core Commands of the MLE-Toolbox 🌱

You are now ready to dive deeper into the specifics of [job configuration](https://roberttlange.github.io/mle-toolbox) and can start running your first experiments from the cluster (or locally on your machine) with the following commands:

|   | Command              |        Description                                                        |
|-----------| -------------------------- | -------------------------------------------------------------- |
|⏳| [`mle init`](https://roberttlange.github.io/mle-toolbox/core_api/mle_init/)       | Start up an experiment.              |
|🚀| [`mle run`](https://roberttlange.github.io/mle-toolbox/core_api/mle_run/)       | Setup of credentials & toolbox settings.              |
|🖥️| [`mle monitor`](https://roberttlange.github.io/mle-toolbox/core_api/mle_monitor/)       | Monitor resource utilisation.              |
|📥	| [`mle retrieve`](https://roberttlange.github.io/mle-toolbox/core_api/mle_retrieve/)       | Retrieve an experiment result.              |
|💌| [`mle report`](https://roberttlange.github.io/mle-toolbox/core_api/mle_report/)       | Create an experiment report with figures.              |
|🔄| [`mle sync-gcs`](https://roberttlange.github.io/mle-toolbox/core_api/mle_sync_gcs/)       | Extract all GCS-stored results to your local drive.              |


## Examples 🎒

|              | Job Types|        Description                                                        |
| -------------------------- |-------------- | -------------------------------------------------------------- |
| 📄 **[Euler PDE](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/numpy_pde)** |  `multi-configs`, `hyperparameter-search`     | Integrate a PDE using forward Euler.              |
| 📄 **[MNIST CNN](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/mnist)**      | `multi-configs`, `hyperparameter-search`     |Train PyTorch MNIST-CNNs.                             |
| 📄 **[JAX VAE](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/jax_vae)**       | `hyperparameter-search`     | Train a JAX-based MNIST VAE. |
| 📄 **[Sklearn SVM](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/sklearn_svm)** | `single-config`     | Train a Sklearn SVM classifier.            |
|  📄 **[Multi Bash](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/bash_configs)**      | `multi-configs`     | Bash based jobs.                        |
| 📄 **[Quadratic PBT](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/pbt_quadratic)**            | `population-based-training`    | PBT on toy quadratic surrogate.                          |
| 📄 **[MNIST PBT](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/pbt_mnist)**            | `population-based-training`     | PBT for a MNIST MLP network.                          |
| 📓 **[Evaluation](https://github.com/RobertTLange/mle-toolbox/tree/main/notebooks/evaluate_results.ipynb)**          | -     | Evaluation of gridsearch results. |
| 📓 **[Testing](https://github.com/RobertTLange/mle-toolbox/tree/main/notebooks/hypothesis_testing.ipynb)**     | -     | Perform hypothesis tests on logs.        |
| 📓 **[GIF Animations](https://github.com/RobertTLange/mle-toolbox/tree/main/notebooks/animate_results.ipynb)** | -     | Walk through a set of animation helpers.      |
|📓 **[PBT Evaluation](https://github.com/RobertTLange/mle-toolbox/tree/main/notebooks/inspect_pbt.ipynb)** | -     | Inspect the result from PBT.                                   |

### Acknowledgements & Citing `mle-toolbox` ✏️

To cite this repository:

```
@software{mle_toolbox2021github,
  author = {Robert Tjarko Lange},
  title = {{MLE-Toolbox}: A Reproducible Workflow for Machine Learning Experiments},
  url = {http://github.com/RobertTLange/mle-toolbox},
  version = {0.3.0},
  year = {2021},
}
```

Much of the `mle-toolbox` design has been inspired by discussions with [Jonathan Frankle](http://www.jfrankle.com/) and [Nandan Rao](https://twitter.com/nandanrao) about the quest for empirically sound and supported claims in Machine Learning. Finally, parts of the `mle <subcommands>` were inspired by Tudor Berariu's [Liftoff package](https://github.com/tudor-berariu/liftoff) and parts of the philosophy by wanting to provide a light-weight version of IDISA's [sacred package](https://github.com/IDSIA/sacred).

## Notes, Development & Questions ❓

- If you find a bug or want a new feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue 🤗
- You can check out the history of release modifications in [`CHANGELOG.md`](https://github.com/RobertTLange/mle-toolbox/blob/main/CHANGELOG.md) (*added, changed, fixed*).
- You can find a set of open milestones in [`CONTRIBUTING.md`](https://github.com/RobertTLange/mle-toolbox/blob/main/CONTRIBUTING.md).
