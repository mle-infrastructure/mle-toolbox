![MLE_Toolbox_Banner](https://github.com/RobertTLange/mle-toolbox/blob/main/docs/thumbnails/mle_thumbnail.png?raw=true)
[![Pyversions](https://img.shields.io/pypi/pyversions/mle-toolbox.svg?style=flat-square)](https://pypi.python.org/pypi/mle-toolbox)[![Docs Latest](https://img.shields.io/badge/docs-dev-blue.svg)](https://github.com/RobertTLange/mle-toolbox/blob/main/docs/how_to_toolbox.md) [![PyPI version](https://badge.fury.io/py/mle-toolbox.svg)](https://badge.fury.io/py/mle-toolbox)

> Coming up with the right research hypotheses is hard - testing them should be easy.

ML researchers need to coordinate different types of experiments on separate remote resources. The *Machine Learning Experiment (MLE)-Toolbox* is designed to facilitate the workflow by providing a simple interface, standardized logging, many common ML experiment types (multi-seed/configurations, grid-searches and hyperparameter optimization pipelines). You can run experiments on your local machine, high-performance compute clusters ([Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html)) as well as on cloud VMs ([GCP](https://cloud.google.com/gcp/)). The results are archived (locally/[GCS bucket](https://cloud.google.com/products/storage/)) and can easily be retrieved or automatically summarized/reported as `.md`/`.html` files.

<span style="color:red">Add **basic example GIF** for toolbox application</span>.

## The 4 Step `mle-toolbox` Cooking Recipe :stew:

1. Follow the [instructions below](#installing-mletoolbox-dependencies) to install the `mle-toolbox` and set up your credentials/configurations.
2. Read the [docs](docs/how_to_toolbox.md) explaining the pillars of the toolbox & the experiment meta-configuration job `.yaml` files .
3. Check out the [examples :page_facing_up:](#examples-getting-started-running-jobs) to get started: Toy [ODE integration](examples/numpy_ode), training [PyTorch MNIST-CNNs](examples/pytorch_mnist) or [VAEs in JAX](examples/jax_vae).
4. Setup  up and run your own experiments using the [template files](templates/) and `mle run <exp_config>.yaml`.


## Installation :memo:

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


#### Setting Up Your Remote Credentials :see_no_evil:

By default the toolbox will only run locally and without any GCS storage of your experiments. If you want to integrate the `mle-toolbox` with your SGE/Slurm clusters, you have to provide additional data. There 2 ways to do so:

1. After installation type `mle init`. This will walk you through all configuration steps in your CLI and save your configuration in `~/mle_config.toml`.
2. Manually edit the [`template_config.toml`](templates/template_config.toml) template. Move/rename the template to your home directory via `mv template_config.toml ~/mle_config.toml`.

The configuration procedure consists of 3 optional steps, which depend on your needs:

1. Set whether to store all results & your database locally or remote in a GCS bucket.
2. Add SGE and/or Slurm credentials & cluster-specific details (headnode, partitions, proxy server, etc.).
3. Add the GCP project, GCS bucket name and database filename to store your results.


## The Core Commands of the MLE-Toolbox :seedling:

You are now ready to dive deeper into the specifics of [job configuration](docs/how_to_toolbox.md) and can start running your first experiments from the cluster (or locally on your machine) with the following commands:

1. **Initial setup of credentials & toolbox settings**: `mle init`
2. **Start up an experiment**: `mle run <exp_config>.yaml`
3. **Monitor resource utilisation**: `mle monitor`
4. **Retrieve an experiment result**: `mle retrieve`
5. **Create an experiment report with figures**: `mle report`
6. **Extract all GCS-stored results to local drive**: `mle sync-gcs`


## Examples :school_satchel:

* :page_facing_up: [Euler PDE](examples/numpy_pde) - Integrate a PDE using forward Euler for different initial conditions.
* :page_facing_up: [MNIST CNN](examples/mnist) - Train CNNs on multiple random seeds & different training configs.
* :page_facing_up: [JAX VAE](examples/jax_vae) - Search through the hyperparameter space of a MNIST VAE.
* :page_facing_up: [Sklearn SVM](examples/sklearn_svm) - Train a SVM classifier to classify low-dimensional digits.
* :page_facing_up: [Multi Bash](examples/bash_configs) - Launch multi-configuration experiments for bash based jobs.
---
- :notebook: [Evaluate Results](notebooks/evaluate_results.ipynb) - Walk through post-processing pipeline (loading/visualization).
- :notebook: [Hypothesis Testing](notebooks/hypothesis_testing.ipynb) - Compare different experiment runs & perform hypothesis tests.
- :notebook: [GIF Animations](notebooks/animate_results.ipynb) - Walk through set of animation helpers.

### Acknowledgements & Citing `mle-toolbox` :pencil2:

To cite this repository:

```
@software{mle_toolbox2021github,
  author = {Robert Tjarko Lange},
  title = {{MLE-Toolbox}: A Reproducible Workflow for Machine Learning Experiments},
  url = {http://github.com/RobertTLange/mle-toolbox},
  version = {1.0.0},
  year = {2021},
}
```

Much of the `mle-toolbox` design has been inspired by discussions with [Jonathan Frankle](http://www.jfrankle.com/) and [Nandan Rao](https://twitter.com/nandanrao) about the quest for empirically sound and supported claims in Machine Learning. Finally, parts of the `mle <subcommands>` were inspired by Tudor Berariu's [Liftoff package](https://github.com/tudor-berariu/liftoff) and parts of the philosophy by wanting to provide a light-weight version of IDISA's [sacred package](https://github.com/IDSIA/sacred).

## Notes, Development & Questions :question:

- If you find a bug or want a new feature, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue :hugs:
- You can check out the history of release modifications in [`CHANGELOG.md`](CHANGELOG.md) (*added, changed, fixed*).
- You can find a set of open milestones in [`CONTRIBUTING.md`](CONTRIBUTING.md).
