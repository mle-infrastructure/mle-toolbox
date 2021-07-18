# Pre-/Post-Processing

*Note*: This page and content is still work in progress!


```yaml
# Parameters for the pre-processing job
pre_processing_args:
    processing_fname: "<run_preprocessing>.py"
    processing_job_args:
        num_logical_cores: 2
        time_per_job: "00:01:00"
    extra_cmd_line_input:
        figures_dir: "experiments/data"

# Parameters for the post-processing job
post_processing_args:
    processing_fname: "<run_postprocessing>.py"
    processing_job_args:
        num_logical_cores: 2
        time_per_job: "00:01:00"
    extra_cmd_line_input:
        figures_dir: "experiments/figures"
```
