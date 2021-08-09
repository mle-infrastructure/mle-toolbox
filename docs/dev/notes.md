# Notes for Development

### Toolbox Philosophy Notes
- Biology protocol: Simply a recipe, or written design, for performing the experiment.
    1. Purpose: Formal statement which encompasses your tested hypothesis.
    2. Materials: What are major items needed to carry out your experiment?
        -> Git commit hash of code repository
    3. Methods: How will you set up your experiment?
        -> Hash of base_config.json
        -> Hash of meta_config.yaml
    4. Controls: What are you going to compare your results with?
        -> Other experiment id or None if no direct comparison
    5. Data Interpretation: What will be done with the data once it is collected?
        -> Generate figures from the experiment results
- Causality tools from Econometrics: Let's be scientific about assessing the impact of algorithmic modifications and performance comparisons.
    - Multiple testing corrections
    - Difference-in-difference estimation - experiment class
    - Power assessment and p-value computation with automatic seed recommendation


### Notes for documentation

- Apply for 1000$ GCP credits: https://edu.google.com/programs/credits/research/?modal_active=none


#### Sun Grid Engine
* [Details on how to submit jobs with qsub](http://bioinformatics.mdc-berlin.de/intro2Unixandmle/sun_grid_engine_for_beginners/how_to_submit_a_job_using_qsub.html)
* [More notes on the SGE system](https://www.osc.edu/supercomputing/batch-processing-at-osc/monitoring-and-managing-your-job)

#### Slurm
* Note that slurm cluster head node allows you to only run 128 processes parallel
    - Need to salloc into a node - figure out max running time!
    - `salloc --job-name "InteractiveJob" --cpus-per-task 8 --mem-per-cpu 1500 --time 20:00:00 --partition standard`
    - git seems to be not working. Remote connection?! add export var to .bashrc
* On Slurm it can make sense to start up a job for the experiment management in a screen/tmux session for monitoring of many jobs:
```
screen
srun --job-name "InteractiveJob" --cpus-per-task 1 --mem-per-cpu 1500 --time 01:00:00 --partition standard --pty bash
```

#### Google Cloud Storage
* Checkout Google Storage Python API: https://googleapis.dev/python/storage/latest/blobs.html
    - How to use gcloud with a proxy server https://stackoverflow.com/questions/43926668/python3-bigquery-or-google-cloud-python-through-http-proxy/43945207#43945207

* How to set up Google Cloud Storage of the experiment log files
    - Create a new project
    - Create a new bucket in the project
    - Set up an authentication key: https://cloud.google.com/docs/authentication/production#passing_variable
    - `pip install google-cloud-storage` and export the Google authentification bath in your .bashrc script
    - Add credentials path to cluster_config.py file & add the project + bucket name
    - Set option whether entire experiment/figure directory should be stored!

#### Toolbox Dependencies
* Pickle DB docs: https://patx.github.io/pickledb/commands.html


## Where to run examples & tests from
- Examples from the `mle_toolbox/examples/` directory.
- Tests from the `mle_toolbox/` directory

## Update docs homepage

- https://squidfunk.github.io/mkdocs-material/creating-your-site/
- https://github.com/squidfunk/mkdocs-material

```
pip install mkdocs-material
mkdocs serve
mkdocs gh-deploy --force
```

## GitHub Actions

- Billing: https://docs.github.com/en/billing/managing-billing-for-github-actions/about-billing-for-github-actions

## Nice visualization tools

- https://favicon.io/favicon-generator/ - For homepage MLE icon
- https://carbon.now.sh/ - for code screenshots
- https://github.com/homeport/termshot - for terminal output screenshots
