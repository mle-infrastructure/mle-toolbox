import os
import yaml
import toml
import commentjson
import pickle
from typing import Union, List
from dotmap import DotMap
# Import helpers for loading meta-log and hyper-log files
from .load_meta_log import load_meta_log
from .load_hyper_log import load_hyper_log
from .helpers import overwrite_config_with_args


def load_mle_toolbox_config():
    """ Load cluster config from the .toml file. See docs for more info. """
    # This assumes that the config file is always named the same way!
    return DotMap(toml.load(os.path.expanduser("~/mle_config.toml")),
                  _dynamic=False)


def load_yaml_config(cmd_args: dict) -> DotMap:
    """ Load in a YAML config file & wrap as DotMap. """
    with open(cmd_args.config_fname) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

    # Update job config with specific cmd args (if provided)
    config = overwrite_config_with_args(config, cmd_args)
    return DotMap(config, _dynamic=False)


def load_json_config(config_fname: str) -> DotMap:
    """ Load in a config JSON file and return as a dictionary """
    json_config = commentjson.loads(open(config_fname, 'r').read())
    dict_config = DotMap(json_config, _dynamic=False)
    return dict_config


def load_pkl_object(filename: str):
    """ Helper to reload pickle objects. """
    with open(filename, 'rb') as input:
        obj = pickle.load(input)
    return obj


def load_result_logs(experiment_dir: str,
                     meta_log_fname: str="meta_log.hdf5",
                     hyper_log_fname: str="hyper_log.pkl"):
    """ Load both meta and hyper logs for an experiment. """
    meta_log = load_meta_log(os.path.join(experiment_dir, meta_log_fname))
    hyper_log = load_hyper_log(os.path.join(experiment_dir, hyper_log_fname))
    return meta_log, hyper_log
