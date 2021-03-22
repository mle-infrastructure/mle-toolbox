import os


def run_hyperparameter_search(meta_job_args: dict,
                              single_job_args: dict,
                              param_search_args: dict):
    """ Run a hyperparameter search experiment. """
    # Import only if used, this will raise an informative error when
    # scikit-optimize is not installed.
    from ..hyperopt import (HyperoptLogger,
                            RandomHyperoptimisation,
                            GridHyperoptimisation,
                            SMBOHyperoptimisation)

    # 1. Setup the hyperlogger for the experiment
    if "hyperlog_fname" in param_search_args.keys():
        hyperlog_fname = os.path.join(meta_job_args.experiment_dir,
                                      param_search_args.hyperlog_fname)
    else:
        hyperlog_fname = os.path.join(meta_job_args.experiment_dir,
                                      "hyper_log.pkl")
    hyper_log = HyperoptLogger(hyperlog_fname,
                               param_search_args.maximize_objective,
                               param_search_args.eval_metrics,
                               param_search_args.verbose_logging,
                               param_search_args.reload_log)

    # 2. Initialize the hyperparameter optimizer class
    search_types = ["random", "grid", "smbo"]

    if param_search_args.search_type == "random":
        hyper_opt = RandomHyperoptimisation(hyper_log, single_job_args,
                                            meta_job_args.base_train_config,
                                            meta_job_args.base_train_fname,
                                            meta_job_args.experiment_dir,
                                            param_search_args.params_to_search,
                                            param_search_args.problem_type,
                                            param_search_args.eval_metrics)

    elif param_search_args.search_type == "grid":
        hyper_opt = GridHyperoptimisation(hyper_log, single_job_args,
                                          meta_job_args.base_train_config,
                                          meta_job_args.base_train_fname,
                                          meta_job_args.experiment_dir,
                                          param_search_args.params_to_search,
                                          param_search_args.problem_type,
                                          param_search_args.eval_metrics)

    elif param_search_args.search_type == "smbo":
        hyper_opt = SMBOHyperoptimisation(hyper_log, single_job_args,
                                          meta_job_args.base_train_config,
                                          meta_job_args.base_train_fname,
                                          meta_job_args.experiment_dir,
                                          param_search_args.params_to_search,
                                          param_search_args.problem_type,
                                          param_search_args.eval_metrics,
                                          param_search_args.smbo_config)

    else:
        raise ValueError("Please provide a valid \
                          hyperparam search type: {}.".format(search_types))

    # 4. Run the jobs
    hyper_opt.run_search(param_search_args.num_search_batches,
                         param_search_args.num_iter_per_batch,
                         param_search_args.num_evals_per_iter)
