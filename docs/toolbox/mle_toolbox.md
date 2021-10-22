# MLE-Toolbox Overview


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
