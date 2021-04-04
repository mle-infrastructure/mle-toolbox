import argparse
from src import run, retrieve, report, monitor, gcs_syn

def main():
    """ Handle argparse/entry point script for all subcommands:
    - `run`: Run a new experiment on a resource available to you.
    - `retrieve`: Retrieve a completed experiment from a cluster/GCS bucket.
    - `report`: Generate a set of reports (.html/.md) from experiment results.
    - `monitor`: Monitor a compute resource and view experiment protocol.
    - `gcs_sync`: Sync all results from Google Cloud Storage
    """
    return
