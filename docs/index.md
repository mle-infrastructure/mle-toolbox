# Welcome to the MLE-Toolbox

<a href="thumbnails/mle_thumbnail.png"><img src="thumbnails/mle_thumbnail.png" width=900 align="center" /></a>

> Coming up with the right research hypotheses is hard - testing them should be easy.

ML researchers need to coordinate different types of experiments on separate remote resources. The *Machine Learning Experiment (MLE)-Toolbox* is designed to facilitate the workflow by providing a simple interface, standardized logging, many common ML experiment types (multi-seed/configurations, grid-searches and hyperparameter optimization pipelines). You can run experiments on your local machine, high-performance compute clusters ([Slurm](https://slurm.schedmd.com/overview.html) and [Sun Grid Engine](http://bioinformatics.mdc-berlin.de/intro2UnixandSGE/sun_grid_engine_for_beginners/README.html)) as well as on cloud VMs ([GCP](https://cloud.google.com/gcp/)). The results are archived (locally/[GCS bucket](https://cloud.google.com/products/storage/)) and can easily be retrieved or automatically summarized/reported as `.md`/`.html` files.


<span style="color:red">Add **basic example GIF** for toolbox application</span>.

## What Does The `mle-toolbox` Provide?

1. API for launching jobs on cluster/cloud computing platforms (Slurm, GridEngine, GCP).
2. Common machine learning research experiment setups:
    - Launching and collecting multiple random seeds in parallel/batches.
    - Hyperparameter searches: Random, Grid, SMBO, Population-Based Training.
    - Pre- and post-processing pipelines for data prep/result visualization.
3. Automated report generation for hyperparameter searches.
4. Storage of results and database in Google Cloud Storage Bucket.
5. Resource monitoring with dashboard visualization.

## 5 Steps To Get Started :stew:

1. Follow the [installation instructions](setup/installation/) and set up your credentials/configurations.
2. Read the [docs](https://roberttlange.github.io/mle-toolbox/) to learn about the toolbox and `.json` & `.yaml` configuration files.
3. Watch the [YouTube Tutorials series](setup/video_tutorials/) for a hands-on walkthrough.
4. Check out and re-run the [examples :page_facing_up:](https://github.com/RobertTLange/mle-toolbox/tree/main/examples) to get comfortable.
5. Run your own experiments using the [template files, project](https://github.com/RobertTLange/mle-project-template) and [`mle run`](https://roberttlange.github.io/mle-toolbox/core_api/mle_run/).


## Core Commands of the Toolbox :seedling:

You are now ready to dive deeper into the specifics of [job configuration](setup/infrastructure/) and can start running your first experiments from the cluster (or locally on your machine) with the commands:

|   | Command              |        Description                                                        |
|-----------| -------------------------- | -------------------------------------------------------------- |
|⏳| [`mle init`](https://roberttlange.github.io/mle-toolbox/core_api/mle_init/)       | Start up an experiment.              |
|🚀| [`mle run`](https://roberttlange.github.io/mle-toolbox/core_api/mle_run/)       | Setup of credentials & toolbox settings.              |
|🖥️| [`mle monitor`](https://roberttlange.github.io/mle-toolbox/core_api/mle_monitor/)       | Monitor resource utilisation.              |
|📥	| [`mle retrieve`](https://roberttlange.github.io/mle-toolbox/core_api/mle_retrieve/)       | Retrieve an experiment result.              |
|💌| [`mle report`](https://roberttlange.github.io/mle-toolbox/core_api/mle_report/)       | Create an experiment report with figures.              |
|🔄| [`mle sync-gcs`](https://roberttlange.github.io/mle-toolbox/core_api/mle_sync_gcs/)       | Extract all GCS-stored results to your local drive.              |
