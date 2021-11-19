```python
# 3. If local - check if experiment should be run on remote resource
if current_resource not in ["sge-cluster", "slurm-cluster"] or (
    current_resource in ["sge-cluster", "slurm-cluster"]
    and resource_to_run is not None
):
    # Ask user on which resource to run on [local/sge/slurm/gcp]
    if cmd_args.resource_to_run is None:
        resource_to_run = ask_for_resource_to_run()

    # If locally launched & want to run on Slurm/SGE - execute on remote!
    if resource_to_run in ["slurm-cluster", "sge-cluster"]:
        if cmd_args.remote_reconnect:
            print_framed("RECONNECT TO REMOTE")
            ssh_manager = SSH_Manager(resource_to_run)
            base, fname_and_ext = os.path.split(cmd_args.config_fname)
            session_name, ext = os.path.splitext(fname_and_ext)
            monitor_remote_session(ssh_manager, session_name)
            return
        else:
            print_framed("TRANSFER TO REMOTE")
            if cmd_args.purpose is not None:
                purpose = " ".join(cmd_args.purpose)
            else:
                purpose = "Run on remote resource"
            run_remote_experiment(
                resource_to_run,
                cmd_args.config_fname,
                job_config.meta_job_args.remote_exec_dir,
                purpose,
            )
            # After successful completion on remote resource - BREAK
            return
```
