# Welcome to the MLE-Toolbox

<a href="thumbnails/mle_thumbnail.png"><img src="thumbnails/mle_thumbnail.png" width=900 align="center" /></a>

> Coming up with the right research hypotheses is hard - testing them should be easy.

ML researchers need to coordinate different types of experiments on separate remote resources. The *Machine Learning Experiment (MLE)-Toolbox* is designed to facilitate the workflow by providing a simple interface, standardized logging, many common ML experiment types (multi-seed/configurations, grid-searches and hyperparameter optimization pipelines). You can run experiments on your local machine, high-performance compute clusters ([Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html)) as well as on cloud VMs ([GCP](https://cloud.google.com/gcp/)). The results are archived (locally/[GCS bucket](https://cloud.google.com/products/storage/)) and can easily be retrieved or automatically summarized/reported as `.md`/`.html` files.


<span style="color:red">Add **basic example GIF** for toolbox application</span>.

## 5 Steps To Get Started :stew:

1. Follow the [installation instructions](setup/installation/) and set up your credentials/configurations.
2. Read the [docs](setup/infrastructure/) to learn about the toolbox and `.json` & `.yaml` configuration files.
3. Watch the [YouTube Tutorials series](setup/video_tutorials/) for a hands-on walkthrough.
4. Check out and re-run the [examples :page_facing_up:](https://github.com/RobertTLange/mle-toolbox/tree/main/examples) to get comfortable.
5. Run your own experiments using the [template files](https://github.com/RobertTLange/mle-toolbox/tree/main/templates) and `mle run <exp_config>.yaml`.


## Core Commands of the Toolbox :seedling:

You are now ready to dive deeper into the specifics of [job configuration](setup/infrastructure/) and can start running your first experiments from the cluster (or locally on your machine) with the commands:

1. **Initial setup of credentials & toolbox settings**: `mle init`
2. **Start up an experiment**: `mle run <exp_config>.yaml`
3. **Monitor resource utilisation**: `mle monitor`
4. **Retrieve an experiment result**: `mle retrieve`
5. **Create an experiment report with figures**: `mle report`
6. **Extract all GCS-stored results to local drive**: `mle sync-gcs`


## Examples :school_satchel:

* :page_facing_up: [Euler ODE](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/ode) - Integrate an ODE using forward Euler for different initial conditions.
* :page_facing_up: [MNIST CNN](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/mnist) - Train CNNs on multiple random seeds & different training configs.
* :page_facing_up: [JAX VAE](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/jax_vae) - Search through the hyperparameter space of a MNIST VAE.
* :page_facing_up: [Sklearn SVM](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/sklearn_svm) - Train a SVM classifier to classify low-dimensional digits.
* :page_facing_up: [Multi Bash](https://github.com/RobertTLange/mle-toolbox/tree/main/examples/bash_configs) - Launch multi-configuration experiments for bash based jobs.
---
- :notebook: [Evaluate Results](https://github.com/RobertTLange/mle-toolbox/tree/main/notebooks/evaluate_results.ipynb) - Walk through post-processing pipeline (loading/visualization).
- :notebook: [Hypothesis Testing](https://github.com/RobertTLange/mle-toolbox/tree/main/notebooks/hypothesis_testing.ipynb) - Compare different experiment runs & perform hypothesis tests.
- :notebook: [GIF Animations](https://github.com/RobertTLange/mle-toolbox/tree/main/notebooks/animate_results.ipynb) - Walk through set of animation helpers.
