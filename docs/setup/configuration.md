# Toolbox Configuration

By default the toolbox will run locally and without any GCS bucket backup of your experiment results. Furthermore, a lightweight PickleDB protocol database of your experiments will not be synced with the cloud version. In the following, we walkthrough how to

1. Enable the execution of jobs on remote resources (cluster/storage) from your local machine.
2. Enable the backing up of your experiment results in a GCS bucket.
3. Enable the backing up of your PickleDB experiment meta log.
4. Enable resource monitoring and dashboard visualization.

**Note**: There are two ways to perform the toolbox configuration:

1. After installation execute `mle init`. This will walk you through all configuration steps in your CLI and save your configuration in `~/mle_config.toml`.
2. Manually edit the [`config_template.toml`](https://github.com/RobertTLange/mle-toolbox/tree/main/config_template.toml) template. Move/rename the template to your home directory via `mv config_template.toml ~/mle_config.toml`.

The configuration procedure consists of 3 optional steps, which depend on your needs:

1. Set whether to store all results & your database locally or remote in a GCS bucket.
2. Add SGE and/or Slurm credentials & cluster-specific details (headnode, partitions, proxy server, etc.).
3. Add the GCP project, GCS bucket name and database filename to store your results.


## Remote Resource Execution

**TBC**

## Google Cloud Storage Backups

**TBC**

## PickleDB Experiment Logging

**TBC**

## Resource Dashboard Monitoring
