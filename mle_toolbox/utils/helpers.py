import os
import pickle
import numpy as np


def print_framed(str_to_print: str, line_width: int = 85, frame_str: str = "="):
    """Add === x === around your string to print."""
    left = np.ceil((line_width - len(str_to_print)) / 2).astype("int") - 2
    right = np.floor((line_width - len(str_to_print)) / 2).astype("int") - 2
    print(left * frame_str + "  " + str_to_print + "  " + right * frame_str)


def save_pkl_object(obj, filename: str):
    """Helper to store pickle objects."""
    with open(filename, "wb") as output:
        # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


def get_os_env_ready(
    num_devices: int = 1,
    mem_prealloc_bool: bool = False,
    mem_prealloc_frac: float = 0.9,
    device_type: str = "cpu",
) -> None:
    """Helper to set up os variables e.g. for Cuda/JAX/XLA experiment."""
    # Set environment variables for usage of CPU cores
    if device_type == "cpu":
        # Set number of devices (CPU cores/GPUs/TPUs) - helps with pmap testing
        os.environ["XLA_FLAGS"] = (
            "--xla_force_host_platform_device_count" + f"={num_devices}"
        )
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        print(f"MLExperiment: Set XLA settings to {num_devices} CPUs.")

    # Set environment variables for usage & memory preallocation on GPU
    if device_type == "gpu":
        # Set visible devices - Jax greedily grabs all availabe devices on node!
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(
            [str(i) for i in range(num_devices)]
        )
        os.environ["XLA_PYTHON_CLIENT_PREALLOCATE"] = (
            "True" if mem_prealloc_bool else "False"
        )
        os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = f"{mem_prealloc_frac}"
        print(f"MLExperiment: Set XLA settings to {num_devices} GPUs.")

    #  Set environment variables for TPU usage - only works for colab
    elif device_type == "tpu":
        import jax.tools.colab_tpu

        jax.tools.colab_tpu.setup_tpu()
