# Welcome to the MLE-Toolbox

<a href="thumbnails/mle_thumbnail.png"><img src="thumbnails/mle_thumbnail.png" width=900 align="center" /></a>

> Coming up with the right research hypotheses is hard - testing them should be easy.

ML researchers need to coordinate different types of experiments on separate remote resources. The *Machine Learning Experiment (MLE)-Toolbox* is designed to facilitate the workflow by providing a simple interface, standardized logging, many common ML experiment types (multi-seed/configurations, grid-searches and hyperparameter optimization pipelines). You can run experiments on your local machine, high-performance compute clusters ([Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html)) as well as on cloud VMs ([GCP](https://cloud.google.com/gcp/)). The results are archived (locally/[GCS bucket](https://cloud.google.com/products/storage/)) and can easily be retrieved or automatically summarized/reported as `.md`/`.html` files.

Download the slide deck [here](slides_mle_pitch.pdf).


## The Core Commands of the MLE-Toolbox :seedling:

You are now ready to dive deeper into the specifics of [job configuration](docs/how_to_toolbox.md) and can start running your first experiments from the cluster (or locally on your machine) with the following commands:

1. **Initial setup of credentials & toolbox settings**: `mle init`
2. **Start up an experiment**: `mle run <exp_config>.yaml`
3. **Monitor resource utilisation**: `mle monitor`
4. **Retrieve an experiment result**: `mle retrieve`
5. **Create an experiment report with figures**: `mle report`
6. **Extract all GCS-stored results to local drive**: `mle sync-gcs`


## Examples :school_satchel:

* :page_facing_up: [Euler ODE](examples/ode) - Integrate an ODE using forward Euler for different initial conditions.
* :page_facing_up: [MNIST CNN](examples/mnist) - Train CNNs on multiple random seeds & different training configs.
* :page_facing_up: [JAX VAE](examples/jax_vae) - Search through the hyperparameter space of a MNIST VAE.
* :page_facing_up: [Sklearn SVM](examples/sklearn_svm) - Train a SVM classifier to classify low-dimensional digits.
* :page_facing_up: [Multi Bash](examples/bash_configs) - Launch multi-configuration experiments for bash based jobs.
---
- :notebook: [Evaluate Results](notebooks/evaluate_results.ipynb) - Walk through post-processing pipeline (loading/visualization).
- :notebook: [Hypothesis Testing](notebooks/hypothesis_testing.ipynb) - Compare different experiment runs & perform hypothesis tests.
- :notebook: [GIF Animations](notebooks/animate_results.ipynb) - Walk through set of animation helpers.
