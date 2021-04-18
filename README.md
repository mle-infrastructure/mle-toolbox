![MLE_Toolbox_Banner](https://github.com/RobertTLange/mle-toolbox/blob/main/docs/mle_thumbnail.png?raw=true)
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-toolbox.svg?style=flat-square)](https://pypi.python.org/pypi/mle-toolbox)[![Docs Latest](https://img.shields.io/badge/docs-dev-blue.svg)](https://github.com/RobertTLange/mle-toolbox/blob/main/docs/how_to_toolbox.md) [![PyPI version](https://badge.fury.io/py/mle-toolbox.svg)](https://badge.fury.io/py/mle-toolbox)

> Coming up with the right research hypotheses is hard - testing them should be easy.

ML researchers need to coordinate different types of experiments on separate remote resources. The Machine Learning Experiment (MLE)-Toolbox is designed to facilitate the workflow by providing a simple interface, standardized logging, many common ML experiment types (multi-seed/configurations, grid-searches and hyperparameter optimization pipelines). You can run experiments on your local machine, on [Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html) clusters. The results are archived (locally/Google Cloud Storage bucket) and can easily retrieved or automatically summarized/reported as `.md`/`.html` files.

## The 4 Step MLE-Toolbox Cooking Recipe

1. Follow the [instructions below](#installing-mletoolbox-dependencies) to install the `mle-toolbox` and set up your credentials/configurations.
2. Read the [docs](docs/how_to_toolbox.md) explaining the pillars of the toolbox & the experiment meta-configuration job `.yaml` files .
3. Check out the [examples :page_facing_up:](#examples-getting-started-running-jobs) to get started: Toy [ODE integration](examples/ode), training [PyTorch MNIST-CNNs](examples/mnist) or [VAEs in JAX](examples/jax_vae).
4. Setup  up and run your own experiments using the [template files](templates/) and `mle run <exp_config>.yaml`.


## Installing `mle_toolbox` & dependencies

If you want to use the toolbox on your local machine follow the instructions locally. Otherwise do so on your respective remote resource (Slurm or SGE). A simple PyPI installation can be done via:

```
pip install mle-toolbox
```

Alternatively, you can clone this repository and afterwards 'manually' install the toolbox and its dependencies (preferably in a clean Python 3.6 environment):

```
git clone https://github.com/RobertTLange/mle-toolbox.git
cd mle-toolbox
pip install -e .
```


## The 5 Core Commands of the MLE-Toolbox

You are now ready to dive deeper into the specifics of [job configuration](docs/how_to_toolbox.md) and can start running your first experiments from the cluster (or locally on your machine) with the following commands:

1. **Initial setup of credentials & toolbox settings**: `mle init`
2. **Start up an experiment**: `mle run <exp_config>.yaml`
3. **Monitor resource utilisation**: `mle monitor`
4. **Retrieve an experiment result**: `mle retrieve`
5. **Create an experiment report with figures**: `mle report`


## Remote Credentials & Toolbox Configuration

By default the toolbox will only run locally and without any GCS storage of your experiments. If you want to integrate the `mle-toolbox` with your SGE/Slurm cluster resources, you have to provide additional data. There are 2 options to do so:

1. After installation type `mle init`. This will walk you through all configuration steps in your CLI and save your configuration in `~/mle_config.toml`.
2. Manually edit the [`template_config.toml`](templates/template_config.toml) template. Move/rename the template to your home directory via `mv template_config.toml ~/mle_config.toml`.


The configuration procedure consists of 4 optional steps, which depend on your needs:

1. Set whether to store all results & your database locally or remote in the GCS bucket.
2. Add the Slurm credentials and cluster-specific details (headnode names, partitions, proxy server for internet) and default job arguments.
3. Add the SGE credentials and cluster-specific details (headnode names, queues, proxy server for internet) and default job arguments.
4. Add the path to your GCP credentials `.json` file, project and GCS bucket name to store your experiment data (as well as protocol database).


## Examples & Getting Your First Job Running

* :page_facing_up: [Euler ODE](examples/ode) - Integrate an ODE using forward Euler for different initial conditions.
* :page_facing_up: [MNIST CNN](examples/mnist) - Train CNNs on multiple random seeds & different training configs.
* :page_facing_up: [JAX VAE](examples/jax_vae) - Search through the hyperparameter space of a MNIST VAE.
* :page_facing_up: [Sklearn SVM](examples/sklearn_svm) - Train a SVM classifier to classify low-dimensional digits.
* :page_facing_up: [Multi Bash](examples/bash_configs) - Launch multi-configuration experiments for bash based jobs.

- :notebook: [Evaluate Results](notebooks/evaluate_results.ipynb) - Walk through post-processing pipeline (loading/visualization).
- :notebook: [GIF Animations](notebooks/animate_results.ipynb) - Walk through set of animation helpers.


## Notes, Development & Questions

- If you find a bug or would like to see a feature implemented, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue :hugs:
- You can check out the history of release modifications in [`CHANGELOG.md`](CHANGELOG.md) (*added, changed, fixed*). 
- You can find a set of open milestones in [`CONTRIBUTING.md`](CONTRIBUTING.md).
