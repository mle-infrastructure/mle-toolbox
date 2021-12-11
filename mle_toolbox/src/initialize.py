import os
import subprocess as sp
import pathlib
import shutil
from datetime import datetime


def initialize(cmd_args):
    """Setup toolbox .toml config. Load in the default and open editor."""
    # Look for toml config and reload it exists - otherwise start w. default
    path_to_store = os.path.expanduser("~/mle_config.toml")
    if os.path.isfile(path_to_store):
        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        overwrite = input(
            time_t
            + " ~/mle_config.toml already exists. Do you want to overwrite it? [Y/N] "
        )
        if overwrite not in ["Y", "y"]:
            return
    path_file = pathlib.Path(__file__).parent.resolve()
    path_norm = os.path.normpath(path_file)
    path_to_load = "/".join(path_norm.split(os.sep)[:-2]) + "/docs/config_template.toml"
    shutil.copy(path_to_load, path_to_store)
    sp.call([os.environ.get("EDITOR", "vim"), path_to_store])
