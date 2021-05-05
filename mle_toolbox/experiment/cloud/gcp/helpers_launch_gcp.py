import time
import subprocess as sp
from dotmap import DotMap
from typing import Union
from .startup_script_gcp import *


cores_to_machine_type = {1: "n2-highcpu-2",
                         2: "c2-standard-4",
                         4: "c2-standard-8",
                         8: "c2-standard-16",
                         15: "c2-standard-30"}

gpu_types = ["nvidia-tesla-p100", "nvidia-tesla-v100", "nvidia-tesla-t4",
             "nvidia-tesla-p4", "nvidia-tesla-k80"]

default_job_arguments = {"job_name": "launch",
                         "use_tpus": False,
                         "num_gpus": 0,
                         "num_logical_cores": 2}


base_gcp_args = DotMap({
                'ZONE': 'us-west1-a',
                'ACCELERATOR_TYPE': None,
                'ACCELERATOR_COUNT': 0,
                'MACHINE_TYPE': 'n2-highcpu-8',
                'IMAGE_NAME': 'c1-deeplearning-tf-2-4-cu110-v20210414-debian-10',
                'IMAGE_PROJECT': 'ml-images',
                })


tpu_gcp_args = DotMap({
                'ZONE': 'europe-west4-a',
                'ACCELERATOR_TYPE': 'v3-8',
                'RUNTIME_VERSION': 'v2-alpha',
                })


def gcp_get_submission_cmd(vm_name: str, job_args: DotMap,
                           startup_fname: str) -> list:
    """ Construct gcloud VM instance creation cmd to execute via cmd line. """
    if job_args.use_tpu:
        job_gcp_args = tpu_gcp_args
    else:
        job_gcp_args = base_gcp_args
        job_gcp_args.MACHINE_TYPE = cores_to_machine_type[job_args.num_logical_cores]
        if job_args.num_gpus > 0:
            job_gcp_args.ACCELERATOR_TYPE = "nvidia-tesla-v100"
            job_gcp_args.ACCELERATOR_COUNT = job_args.num_gpus

    if job_args.use_tpu:
        # TPU VM Alpha gcloud create CMD
        gcp_launch_cmd = [
            'gcloud', 'alpha', 'compute', 'tpus', 'tpu-vm', 'create',
            f'{vm_name}',
            f'--preemptible',
            f'--zone={job_gcp_args.ZONE}',
            f'--accelerator-type={job_gcp_args.ACCELERATOR_TYPE}',
            f'--version={job_gcp_args.RUNTIME_VERSION}',
            f'--metadata-from-file=startup-script={startup_fname}',
            '--no-user-output-enabled', '--verbosity', 'error'
                    ]
    else:
        # CPU VM gcloud create CMD w/o any GPU attached
        gcp_launch_cmd = [
            'gcloud', 'compute', 'instances', 'create',
            f'{vm_name}',
            f'--preemptible',
            f'--zone={job_gcp_args.ZONE}',
            f'--machine-type={job_gcp_args.MACHINE_TYPE}',
            f'--image={job_gcp_args.IMAGE_NAME}',
            f'--image-project={job_gcp_args.IMAGE_PROJECT}',
            f'--metadata-from-file=startup-script={startup_fname}',
            '--scopes=cloud-platform,storage-full',
            '--boot-disk-size=128GB',
            '--boot-disk-type=pd-standard',
            '--no-user-output-enabled', '--verbosity', 'error'
                    ]

        # Attach GPUs to Job if desired - make sure to install nvidia driver
        if (job_gcp_args.ACCELERATOR_COUNT > 0 and
            job_gcp_args.ACCELERATOR_TYPE is not None):
            gcp_launch_cmd += [
            '--metadata=install-nvidia-driver=True'
            '--maintenance-policy=TERMINATE',
            f'--accelerator=type={job_gcp_args.ACCELERATOR_TYPE},'
            + f'count={job_gcp_args.ACCELERATOR_COUNT}'
            ]

    return gcp_launch_cmd, job_gcp_args


def gcp_generate_startup_file(remote_code_dir: str,
                              remote_results_dir: str,
                              job_filename: str,
                              config_filename: str,
                              experiment_dir: str,
                              startup_fname: str,
                              gcp_bucket_name: str,
                              use_tpu: bool=False,
                              use_cuda: bool=False) -> str:
    """ Generate bash script template to launch at VM startup. """
    # Build the start job execution script
    # 1. Connecting to tmux via: gcloud compute ssh $VM -- /sudo_tmux_a.sh
    # 2a. Launch venv & install dependencies from requirements.txt
    # 2b. [OPTIONAL] Setup JAX TPU build
    # 3. Separate tmux split for rsync of results to GCS bucket
    startup_script_content = (
                "#!/bin/bash" +
                tmux_setup +
                clone_gcp_bucket_dir.format(
                    remote_dir=remote_code_dir,
                    gcp_bucket_name=gcp_bucket_name) +
                install_venv.format(
                    remote_dir=remote_code_dir)
                )

    if use_tpu:
        # Install TPU version JAX
        startup_script_content += jax_tpu_build
    elif use_cuda:
        # Install GPU version JAX
        startup_script_content += jax_gpu_build

    startup_script_content += (exec_python.format(
                                remote_dir=remote_code_dir,
                                job_filename=job_filename,
                                config_filename=config_filename,
                                experiment_dir=experiment_dir,
                                seed_id=0) +
                               sync_results_from_dir.format(
                                remote_code_dir=remote_code_dir,
                                remote_results_dir=remote_results_dir,
                                gcp_bucket_name=gcp_bucket_name,
                                experiment_dir=experiment_dir)
                               )

    # Write startup script to physical file
    with open(startup_fname, 'w', encoding='utf8') as f:
        f.write(startup_script_content)


def gcp_delete_vm_instance(vm_name: str, vm_zone: str, use_tpu: bool=False):
    """ Quitely delete job by its name + zone. TODO: Add robustness check. """
    if not use_tpu:
        gcp_delete_cmd = ['gcloud', 'compute', 'instances', 'delete',
                          f'{vm_name}', '--zone', f'{vm_zone}', '--quiet',
                          '--no-user-output-enabled', '--verbosity', 'error']
    else:
        gcp_delete_cmd = ['gcloud', 'alpha', 'compute', 'tpus', 'tpu-vm',
                          'delete', f'{vm_name}', '--zone', f'{vm_zone}',
                          '--quiet', '--no-user-output-enabled',
                          '--verbosity', 'error']
    sp.run(gcp_delete_cmd)
