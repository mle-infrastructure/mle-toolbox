import os


def compose_protocol_data(job_config: dict, resource_to_run: str, purpose: str):
    """Prepare experiment data to be stored in `MLEProtocol`."""
    # Get base working directory and experiment directory
    experiment_dir = os.path.join(
        os.getcwd(), job_config.meta_job_args["experiment_dir"]
    )

    # Extract the number of seeds over which experiment is run
    if job_config.meta_job_args["experiment_type"] == "hyperparameter-search":
        num_seeds = job_config.param_search_args.search_resources[
            "num_seeds_per_eval"
        ]
    elif job_config.meta_job_args["experiment_type"] == "multiple-configs":
        if "num_seeds" in job_config.multi_config_args.keys():
            num_seeds = job_config.multi_config_args["num_seeds"]
        else:
            num_seeds = len(job_config.multi_config_args["random_seeds"])
    else:
        num_seeds = 1

    # Get total number of jobs and number of sequential batches
    if job_config.meta_job_args["experiment_type"] == "hyperparameter-search":
        search_resources = job_config.param_search_args["search_resources"]
        try:
            if (
                job_config.param_search_args["search_config"]["search_schedule"]
                == "sync"
            ):
                num_total_jobs = (
                    search_resources["num_search_batches"]
                    * search_resources["num_evals_per_batch"]
                    * search_resources["num_seeds_per_eval"]
                )
                num_job_batches = search_resources["num_search_batches"]
                num_jobs_per_batch = (
                    search_resources["num_evals_per_batch"]
                    * search_resources["num_seeds_per_eval"]
                )
            else:
                num_total_jobs = (
                    search_resources["num_total_evals"]
                    * search_resources["num_seeds_per_eval"]
                )
                num_job_batches = 1
                num_jobs_per_batch = search_resources["max_running_jobs"]
        except Exception:
            try:
                num_total_jobs = (
                    search_resources["num_search_batches"]
                    * search_resources["num_evals_per_batch"]
                    * search_resources["num_seeds_per_eval"]
                )
                num_job_batches = search_resources["num_search_batches"]
                num_jobs_per_batch = (
                    search_resources["num_evals_per_batch"]
                    * search_resources["num_seeds_per_eval"]
                )
            except Exception:
                num_total_jobs, num_job_batches, num_jobs_per_batch = 0, 0, 0
    elif job_config.meta_job_args["experiment_type"] == "multiple-configs":
        num_total_jobs = (
            len(job_config.multi_config_args["config_fnames"]) * num_seeds
        )
        num_job_batches = 1
        num_jobs_per_batch = num_total_jobs
    else:
        num_total_jobs = 1
        num_job_batches = 1
        num_jobs_per_batch = 1

    # Get job duration, number of cores and gpus per job
    num_cpus = job_config.single_job_args["num_logical_cores"]
    try:
        num_gpus = job_config.single_job_args["num_gpus"]
    except Exception:
        num_gpus = 0

    try:
        time_per_job = job_config.single_job_args["time_per_job"]
    except Exception:
        time_per_job = "01:00:00"

    meta_data = {
        "purpose": purpose,
        "exec_resource": resource_to_run,
        "project_name": job_config.meta_job_args["project_name"],
        "experiment_dir": experiment_dir,
        "experiment_type": job_config.meta_job_args["experiment_type"],
        "base_fname": job_config.meta_job_args["base_train_fname"],
        "config_fname": job_config.meta_job_args["base_train_config"],
        "num_seeds": num_seeds,
        "num_total_jobs": num_total_jobs,
        "num_job_batches": num_job_batches,
        "num_jobs_per_batch": num_jobs_per_batch,
        "time_per_job": time_per_job,
        "num_cpus": num_cpus,
        "num_gpus": num_gpus,
    }

    extra_data = {}
    extra_data["single_job_args"] = job_config.single_job_args.toDict()
    extra_data["meta_job_args"] = job_config.meta_job_args.toDict()
    if job_config.meta_job_args["experiment_type"] == "hyperparameter-search":
        extra_data["job_spec_args"] = job_config.param_search_args.toDict()
    return meta_data, extra_data
