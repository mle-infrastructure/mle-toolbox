# Lightweight Distributed ML Experiments Management 🛠️
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-toolbox.svg?style=flat-square)](https://pypi.python.org/pypi/mle-toolbox)
[![Docs Latest](https://img.shields.io/badge/docs-dev-blue.svg)](https://roberttlange.github.io/mle-toolbox/)
[![PyPI version](https://badge.fury.io/py/mle-toolbox.svg)](https://badge.fury.io/py/mle-toolbox)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Status](https://github.com/mle-infrastructure/mle-toolbox/workflows/Python%20tests/badge.svg)](https://github.com/mle-infrastructure/mle-toolbox/actions?query=workflow%3A"Python+tests")
[![codecov](https://codecov.io/gh/mle-infrastructure/mle-toolbox/branch/main/graph/badge.svg?token=0B56UIWGX3)](https://codecov.io/gh/mle-infrastructure/mle-toolbox)
[![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-toolbox/blob/main/notebooks/getting_started.ipynb)
<a href="https://github.com/mle-infrastructure/mle-toolbox/blob/main/docs/logo_transparent.png?raw=true"><img src="https://github.com/mle-infrastructure/mle-toolbox/blob/main/docs/logo_transparent.png?raw=true" width="200" align="right" /></a>

> Coming up with the right hypothesis is hard - testing it should be easy.

ML researchers need to coordinate different types of experiments on separate remote resources. The *Machine Learning Experiment (MLE)-Toolbox* is designed to facilitate the workflow by providing a simple interface, standardized logging, many common ML experiment types (multi-seed/configurations, grid-searches and hyperparameter optimization pipelines). You can run experiments on your local machine, high-performance compute clusters ([Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html)) as well as on cloud VMs ([GCP](https://cloud.google.com/gcp/)). The results are archived (locally/[GCS bucket](https://cloud.google.com/products/storage/)) and can easily be retrieved or automatically summarized/reported.

<a href="https://github.com/mle-infrastructure/mle-toolbox/blob/main/docs/mle_run.gif?raw=true"><img src="https://github.com/mle-infrastructure/mle-toolbox/blob/main/docs/mle_run.gif?raw=true" width="800" align="right" /></a>

## What Does The `mle-toolbox` Provide? 🧑‍🔧

1. API for launching jobs on cluster/cloud computing platforms (Slurm, GridEngine, GCP).
2. Common machine learning research experiment setups:
    - Launching and collecting multiple random seeds in parallel/batches or async.
    - Hyperparameter searches: Random, Grid, SMBO, PBT and Nevergrad.
    - Pre- and post-processing pipelines for data preparation/result visualization.
3. Automated report generation for hyperparameter search experiments.
4. Storage/retrieval of results and database in Google Cloud Storage Bucket.
5. Resource monitoring with dashboard visualization.

![](https://github.com/mle-infrastructure/mle-toolbox/blob/main/docs/mle_toolbox_structure.png?raw=true)

## The 4 Step `mle-toolbox` Cooking Recipe 🍲

1. Follow the [instructions below](https://github.com/mle-infrastructure/mle-toolbox#installation-) to install the `mle-toolbox` and set up your credentials/configuration.
2. Read the [docs](https://mle-infrastructure.github.io) explaining the pillars of the toolbox & the experiment meta-configuration job `.yaml` files .
3. Learn more about the individual infrastructure subpackages with the [dedicated tutorial](https://github.com/mle-infrastructure/mle-tutorial).
4. Check out the [examples 📄](https://github.com/mle-infrastructure/mle-toolbox#examples-) to get started: [Single Objective Optimization](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/toy_single_objective), [Multi Objective Optimization](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/toy_multi_objective).
5. Run your own experiments using the [template files, project](https://github.com/mle-infrastructure/mle-project) and [`mle run`](https://mle-infrastructure.github.io/mle_toolbox).


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

## The Core Toolbox Subcommands 🌱

You are now ready to dive deeper into the specifics of [experiment configuration](https://mle-infrastructure.github.io/mle_toolbox/experiments/) and can start running your first experiments from the cluster (or locally on your machine) with the following commands:

|   | Command              |        Description                                                        |
|-----------| -------------------------- | -------------------------------------------------------------- |
|🚀| `mle run`      | Start up an experiment (multi-config/seeds, search).              |
|🖥️| `mle monitor`       | Monitor resource utilisation ([`mle-monitor`](https://github.com/mle-infrastructure/mle-monitor) wrapper).              |
|📥	| `mle retrieve`       | Retrieve experiment result from GCS/cluster.              |
|💌| `mle report`       | Create an experiment report with figures.              |
|⏳| `mle init`       | Setup of credentials & toolbox settings.              |
|🔄| `mle sync`       | Extract all GCS-stored results to your local drive.              |
|🗂| `mle project`    | Initialize a new project by cloning [`mle-project`](https://github.com/mle-infrastructure/mle-project).   
|📝| `mle protocol`    | List a summary of the most recent experiments.

You can find more documentation for each subcommand [here](https://mle-infrastructure.github.io/mle_toolbox/subcommands/).

## Examples 📄 & Notebook Walkthroughs 📓

|              | Job Types|        Description                                                        |
| -------------------------- |-------------- | -------------------------------------------------------------- |
| 📄 **[Single-Objective](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/toy_single_objective)** |  `multi-configs`, `hyperparameter-search`     | Core experiment types.              |
| 📄 **[Multi-Objective](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/toy_multi_objective)**       | `hyperparameter-search`     | Multi-objective tuning. |
|  📄 **[Multi Bash](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/bash_multi_config)**      | `multi-configs`     | Bash-based jobs.                        |
| 📄 **[Quadratic PBT](https://github.com/mle-infrastructure/mle-toolbox/tree/main/examples/pbt_quadratic)**            | `population-based-training`    | PBT on toy quadratic surrogate.                          |

|              | Description|        Colab                                                        |
| -------------------------- |-------------- | -------------------------------------------------------------- |
| 📓 **[Getting Started](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/getting_started.ipynb)**          |  Get started with the toolbox. | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-toolbox/blob/main/notebooks/getting_started.ipynb)
| 📓 **[Subpackages](https://github.com/mle-infrastructure/mle-tutorial/tree/main/tutorial.ipynb)**          |  Get started with the toolbox subpackages. | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-toolbox/blob/main/notebooks/getting_started.ipynb)
| 📓 **[Evaluation](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/evaluate_results.ipynb)**          |  Evaluation of gridsearch results. | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-toolbox/blob/main/notebooks/evaluate_results.ipynb)
| 📓 **[GIF Animations](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/animate_results.ipynb)** |  Walk through a set of animation helpers.      | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-toolbox/blob/main/notebooks/animate_results.ipynb)
| 📓 **[Testing](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/hypothesis_testing.ipynb)**     | Perform hypothesis tests on logs.        | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-toolbox/blob/main/notebooks/experimental/hypothesis_testing.ipynb)
|📓 **[PBT Evaluation](https://github.com/mle-infrastructure/mle-toolbox/tree/main/notebooks/inspect_pbt.ipynb)** | Inspect the result from PBT.   | [![Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mle-infrastructure/mle-toolbox/blob/main/notebooks/experimental/inspect_pbt.ipynb)

### Acknowledgements & Citing the MLE-Infrastructure ✏️

If you use parts the `mle-toolbox` in your research, please cite it as follows:

```
@software{mle_infrastructure2021github,
  author = {Robert Tjarko Lange},
  title = {{MLE-Infrastructure}: A Set of Lightweight Tools for Distributed Machine Learning Experimentation},
  url = {http://github.com/mle-infrastructure},
  year = {2021},
}
```

Much of the `mle-toolbox` design has been inspired by discussions with [Jonathan Frankle](http://www.jfrankle.com/) and [Nandan Rao](https://twitter.com/nandanrao) about the quest for empirically sound and supported claims in Machine Learning. Finally, parts of the `mle <subcommands>` were inspired by Tudor Berariu's [Liftoff package](https://github.com/tudor-berariu/liftoff) and parts of the philosophy by wanting to provide a light-weight version of IDISA's [sacred package](https://github.com/IDSIA/sacred). Further credit goes to [Facebook's `submitit`](https://github.com/facebookincubator/submitit) and [Ray](https://github.com/ray-project/ray).

## Notes, Development & Questions ❓

- If you find a bug or want a new feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue 🤗
- You can check out the history of release modifications in [`CHANGELOG.md`](https://github.com/RobertTLange/mle-toolbox/blob/main/CHANGELOG.md) (*added, changed, fixed*).
- You can find a set of open milestones in [`CONTRIBUTING.md`](https://github.com/RobertTLange/mle-toolbox/blob/main/CONTRIBUTING.md).
