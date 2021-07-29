# Toolbox Infrastructure

In this document you can learn everything about how to run experiments with the `mle-toolbox`. The `mle-toolbox` allows you to run different types of experiments locally or on an SGE cluster. You have to provide three inputs:

1. An experiment/meta configuration `.yaml` file.
2. A job configuration `.json`file.
3. A python `.py` script that runs your training loop.

<a href="toolbox-schematic.png"><img src="toolbox-schematic.png" width=900 align="center" /></a>


The only things you have to do is specify your desired experiment. The toolbox automatically detects whether you start an experiment with access to multiple compute nodes.

- `train.py` takes three arguments: `-config`, `-seed`, `-exp_dir`
- This includes the standard inputs to the training function (`model_config`, `train_config`, `log_config`) but can be otherwise generalised to your applications.

<a href="toolbox-inputs.png"><img src="toolbox-inputs.png" width=900 align="center" /></a>


# Jobs, Evals and Experiments

Throughout the toolbox we refer to different granularities of compute loads. It helps being familiar with what these refer to (from lowest to highest level of specification):

- **job**: A single submission process on resource (e.g. one seed for one configuration)
- **eval**: A single parameter configuration which can be executed/trained for multiple seeds (individual jobs!)
- **experiment**: An entire sequence of jobs to be executed (e.g. grid search with pre/post-processing)


# Protocol DB Logging

**TBC**

# Rich Dashboard Monitoring

**TBC**

# Experiment Report Summarization

**TBC**
