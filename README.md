# Machine Learning Experiment (MLE) Toolbox
## Coordinate Local, Slurm, SunGridEngine and GCP Experiments

Coming up with the right hypothesis to test is hard - testing them should be easy. Often times one needs to coordinate different types of experiments on separate remote resources. 
The MLE-Toolbox is designed to facilitate your workflow providing a common interface, standardized logging, many common experiment types (multi-seed/-config runs, gridsearches and hyperparameter optimization pipelines) as well as an easy retrieval of results. You can run experiments on your local machine, on [Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html) clusters as well as [Google Cloud compute instances](https://cloud.google.com/compute/docs/instances?hl=en).


Here are 3 steps to get started with running your distributed jobs:

1. Follow the [instructions below](#installing-mletoolbox-dependencies) to install the `mle-toolbox` and to set up your credentials/configurations.
2. Read the [documentation](mle_toolbox/docs/how_to_toolbox.md) explaining the pillars of the toolbox & how to compose the meta-configuration job `.yaml` files for your experiments.
3. Check out the [examples :notebook:](#examples-getting-started-running-jobs) to get started with a toy [ODE integration](mle_toolbox/examples/ode), [MNIST-CNN training](mle_toolbox/examples/mnist) or an example of how to train a [PPO agent](mle_toolbox/examples/ppo).


## Installing `mle_toolbox` & dependencies

If you want to use the toolbox on your local machine follow the instructions locally. Otherwise do so on your respective remote resource (Slurm, SGE, or GCP). A simple PyPI installation can be done via:

```
pip install mle-toolbox
```

Alternatively, you can clone this repository and afterwards 'manually' install the toolbox (preferably in a clean Python 3.6 environment):

```
git clone https://github.com/RobertTLange/mle-toolbox.git
cd mle-toolbox
pip install -e .
```

This will install all required dependencies. Please note that the toolbox is tested only for Python 3.6.

## Setting up your Remote Credentials & Configuration

By default the toolbox will only run locally and without any GCS storage of your experiments. If you want to integrate the `mle-toolbox` with your remote resources, please edit the [`cluster_config.py`](mle_toolbox/docs/template_config.py) template. This consists of 4 optional steps:

1. Set whether or not you want to store all results and your database locally or remote in the Google Cloud Storage bucket.
2. Add the Slurm credentials as well as cluster-specific details (headnode names, partitions, proxy server for internet) and default job arguments.
3. Add the SGE credentials as well as cluster-specific details (headnode names, queues, proxy server for internet) and default job arguments.
4. Add the path to your GCP credentials `.json` file as well as project and GCS bucket name to store your experiment data (as well as protocol database).

Afterwards, please move and rename the template to the `mle-toolbox/mle_toolbox` directory as `cluster_config.py`.

```
mv mle_toolbox/docs/template_config.py mle_toolbox/cluster_config.py
``` 

*Note*: If you only intend to use a single resource, then simply only update the configuration for that resource.

## The 4 Commands of the Toolbox

You are now ready to dive deeper into the specifics of [job configuration](mle_toolbox/docs/how_to_toolbox.md) and can start running your first experiments from the cluster (or locally on your machine) with the following commands:

1. **Start up an experiment**: `run-experiment <experiment_config>.yaml`
2. **Monitor resource utilisation**: `monitor-cluster`
3. **Retrieve the experiment results**: `retrieve-experiment`
4. **Create a one-page experiment report**: `report-experiment`

## Examples & Getting Your First Job Running

* :notebook: [Euler ODE](mle_toolbox/examples/ode) - Integrate a simple ODE using forward Euler & get to know the toolbox.
* :notebook: [MNIST CNN](mle_toolbox/examples/mnist) - Train a CNN on multiple random seeds & different training configurations.
* :notebook: [Pendulum PPO](mle_toolbox/examples/ppo) - Search through the hyperparameter space of a PPO agent.

The PPO examples depend on another package of mine: [drl-toolbox](https://github.com/RobertTLange/drl-toolbox). **Note**: This has not been open-sourced yet. Contact me if you want to run it!

## Development & Questions

* If you find a bug or would like to see a feature implemented, feel free to contact me [@RobertTLange](https://twitter.com/RobertTLange) or create an issue :hugs:
* You can run all unit/integration tests from `mle_toolbox/` with `pytest` (run locally & remote).
* [Details on how to submit jobs with qsub](http://bioinformatics.mdc-berlin.de/intro2Unixandmle/sun_grid_engine_for_beginners/how_to_submit_a_job_using_qsub.html)
* [More notes on the SGE system](https://www.osc.edu/supercomputing/batch-processing-at-osc/monitoring-and-managing-your-job)
