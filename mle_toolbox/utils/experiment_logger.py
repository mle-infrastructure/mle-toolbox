import numpy as np
import pandas as pd

import os
import shutil
import pickle
import time
import datetime
import h5py
from typing import Union, List


class DeepLogger(object):
    """
    Logging object for Deep Learning experiments

    Args:
        time_to_track (List[str]): column names of pandas df - time
        what_to_track (List[str]): column names of pandas df - statistics
        time_to_print (List[str]): columns of time df to print out
        what_to_print (List[str]): columns of stats df to print out
        config_fname (str): file path of configuration of experiment
        experiment_dir (str): base experiment directory
        tboard_fname (str): base name of tensorboard
        use_tboard (bool): whether to log to tensorboard
        print_every_k_updates (int): after how many log updates - verbose
        seed_id (str): seed id to distinguish logs with
        model_type (str): ["torch", "jax", "sklearn"] - tboard/storage
        save_every_k_ckpt (int): save every other checkpoint
        overwrite_experiment_dir (bool): delete old log file/tboard dir
    """

    def __init__(self,
                 time_to_track: List[str],
                 what_to_track: List[str],
                 time_to_print: List[str],
                 what_to_print: List[str],
                 config_fname: str,
                 experiment_dir: str = "/",
                 tboard_fname: Union[str, None] = None,
                 use_tboard: bool=False,
                 print_every_k_updates: Union[int, None] = None,
                 seed_id: Union[str, None] = None,
                 model_type: str = "default",
                 save_every_k_ckpt: Union[int, None] = None,
                 overwrite_experiment_dir: bool = False):
        # Initialize counters of log
        self.log_update_counter = 0
        self.log_save_counter = 0
        self.model_save_counter = 0
        self.print_every_k_updates = print_every_k_updates

        # Type of model to log/store
        self.model_type = model_type

        # Store every k-th checkpoint
        self.save_every_k_ckpt = save_every_k_ckpt

        # Set up the logging directories - save the timestamped config file
        self.setup_experiment_dir(experiment_dir, config_fname, seed_id,
                                  use_tboard, tboard_fname,
                                  overwrite_experiment_dir)

        # Initialize pd dataframes to store logging stats/times
        self.time_to_track = time_to_track + ["time_elapsed"]
        self.what_to_track = what_to_track
        self.clock_to_track = pd.DataFrame(columns=self.time_to_track)
        self.stats_to_track = pd.DataFrame(columns=self.what_to_track)

        # Set up what to print
        self.time_to_print = time_to_print
        self.what_to_print = what_to_print
        self.verbose = len(self.what_to_print) > 0

        # Start stop-watch/clock of experiment
        self.start_time = time.time()

    def setup_experiment_dir(self,
                             base_exp_dir: str,
                             config_fname: Union[str, None],
                             seed_id: Union[str, None],
                             use_tboard: bool=False,
                             tboard_fname: Union[str, None]=None,
                             overwrite_experiment_dir: bool = False):
        """ Setup a directory for experiment & copy over config. """
        # Get timestamp of experiment & create new directories
        timestr = datetime.datetime.today().strftime("%Y-%m-%d")[2:] + "_"
        base_str = os.path.split(config_fname)[1].split(".")[0]
        self.base_str = base_str
        self.experiment_dir = os.path.join(base_exp_dir, timestr + base_str + "/")

        # Create a new empty directory for the experiment
        if not os.path.exists(self.experiment_dir):
            try: os.makedirs(self.experiment_dir)
            except: pass

        if not os.path.exists(os.path.join(self.experiment_dir, "logs/")):
            try: os.makedirs(os.path.join(self.experiment_dir, "logs/"))
            except: pass

        if not os.path.exists(os.path.join(self.experiment_dir, "models/")):
            try: os.makedirs(os.path.join(self.experiment_dir, "models/"))
            except: pass

        # Create separate sub-dictionaries for checkpoints & final trained model
        if self.save_every_k_ckpt is not None:
            if not os.path.exists(os.path.join(self.experiment_dir, "models/final/")):
                try: os.mkdir(os.path.join(self.experiment_dir, "models/final/"))
                except: pass
            if not os.path.exists(os.path.join(self.experiment_dir, "models/ckpt/")):
                try: os.mkdir(os.path.join(self.experiment_dir, "models/ckpt/"))
                except: pass

        exp_time_base = self.experiment_dir + timestr + base_str
        self.config_copy = exp_time_base + ".json"
        if not os.path.exists(self.config_copy):
            shutil.copy(config_fname, self.config_copy)

        if seed_id is None:
            exp_time_base_ext = exp_time_base
        else:
            exp_time_base_ext = exp_time_base + "_" + seed_id

        # Set where to log to (Stats - .hdf5, model - .ckpth)
        self.log_save_fname = (self.experiment_dir + "logs/" +
                               timestr + base_str + "_" + seed_id
                               + ".hdf5")

        # Create separate filenames for checkpoints & final trained model
        if self.save_every_k_ckpt is not None:
            self.final_model_save_fname = (self.experiment_dir + "models/final/" +
                                             timestr + base_str + "_" + seed_id)
            self.ckpt_model_save_fname = (self.experiment_dir + "models/ckpt/" +
                                             timestr + base_str + "_" + seed_id)
        else:
            self.final_model_save_fname = (self.experiment_dir + "models/" +
                                             timestr + base_str + "_" + seed_id)

        # Different extensions to model checkpoints based on model type
        if self.model_type == "torch":
            self.final_model_save_fname += ".pt"
        elif self.model_type in ["jax", "sklearn"]:
            self.final_model_save_fname += ".pkl"

        # Delete old log file and tboard dir if overwrite allowed
        if overwrite_experiment_dir:
            if os.path.exists(self.log_save_fname):
                os.remove(self.log_save_fname)
            if use_tboard:
                if os.path.exists(self.experiment_dir + "tboards/"):
                    shutil.rmtree(self.experiment_dir + "tboards/")
        self.seed_id = seed_id

        # Initialize tensorboard logger/summary writer
        if tboard_fname is not None and use_tboard:
            try:
                from tensorboardX import SummaryWriter
            except ModuleNotFoundError as err:
                raise ModuleNotFoundError(f"{err}. You need to install "
                                          "`tensorboardX` if you want that "
                                          "DeepLogger logs to tensorboard.")
            self.writer = SummaryWriter(self.experiment_dir + "tboards/" +
                                        tboard_fname + "_" + seed_id)
        else:
            self.writer = None

    def update_log(self,
                   clock_tick: list,
                   stats_tick: list,
                   model=None,
                   plot_to_tboard=None,
                   save=False):
        """ Update with the newest tick of performance stats, net weights """
        # Transform clock_tick, stats_tick lists into pd arrays
        c_tick = pd.DataFrame(columns=self.time_to_track)
        c_tick.loc[0] = clock_tick + [time.time() - self.start_time]
        s_tick = pd.DataFrame(columns=self.what_to_track)
        s_tick.loc[0] = stats_tick

        # Append time tick & results to pandas dataframes
        self.clock_to_track = pd.concat([self.clock_to_track, c_tick], axis=0)
        self.stats_to_track = pd.concat([self.stats_to_track, s_tick], axis=0)

        # Tick up the update counter
        self.log_update_counter += 1

        # Update the tensorboard log with the newest event
        if self.writer is not None:
            self.update_tboard(clock_tick, stats_tick, model, plot_to_tboard)

        # Print the most current results
        if self.verbose and self.print_every_k_updates is not None:
            if self.log_update_counter % self.print_every_k_updates == 0:
                print(pd.concat([c_tick[self.time_to_print],
                                 s_tick[self.what_to_print]], axis=1))

        # Save the log if boolean says so
        if save:
            self.save_log()
            # Save the most recent model checkpoint
            if model is not None:
                self.save_model(model)

    def update_tboard(self,
                      clock_tick: list,
                      stats_tick: list,
                      model = None,
                      plot_to_tboard = None):
        """ Update the tensorboard with the newest events """
        # Add performance & step counters
        for i, performance_tick in enumerate(self.what_to_track):
            self.writer.add_scalar('performance/' + performance_tick,
                                   np.mean(stats_tick[i]), clock_tick[0])

        # Log the model params & gradients
        if model is not None:
            for name, param in model.named_parameters():
                self.writer.add_histogram('weights/' + name,
                                          param.clone().cpu().data.numpy(),
                                          clock_tick[0])
                self.writer.add_histogram('gradients/' + name,
                                          param.grad.clone().cpu().data.numpy(),
                                          clock_tick[0])

        # Add the plot of interest to tboard
        if plot_to_tboard is not None:
            self.writer.add_figure('plot', plot_to_tboard, stats_tick[i])

        # Flush the log event
        self.writer.flush()

    def save_log(self):
        """ Create compressed .hdf5 file containing group <random-seed-id> """
        h5f = h5py.File(self.log_save_fname, 'a')

        # Create "datasets" to store in the hdf5 file [time, stats]
        # Store all relevant meta data (log filename, checkpoint filename)
        if self.log_save_counter == 0:
            h5f.create_dataset(name=self.seed_id + "/meta/model_ckpt",
                               data=[self.final_model_save_fname.encode("ascii", "ignore")],
                               compression='gzip', compression_opts=4,
                               dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/log_paths",
                               data=[self.log_save_fname.encode("ascii", "ignore")],
                               compression='gzip', compression_opts=4,
                               dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/experiment_dir",
                               data=[self.experiment_dir.encode("ascii", "ignore")],
                               compression='gzip', compression_opts=4,
                               dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/config_fname",
                               data=[self.config_copy.encode("ascii", "ignore")],
                               compression='gzip', compression_opts=4,
                               dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/eval_id",
                               data=[self.base_str.encode("ascii", "ignore")],
                               compression='gzip', compression_opts=4,
                               dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/model_type",
                               data=[self.model_type.encode("ascii", "ignore")],
                               compression='gzip', compression_opts=4,
                               dtype='S200')

        # Store all time_to_track variables
        for o_name in self.time_to_track:
            if self.log_save_counter >= 1:
                if h5f.get(self.seed_id + "/time/" + o_name):
                    del h5f[self.seed_id + "/time/" + o_name]
            h5f.create_dataset(name=self.seed_id + "/time/" + o_name,
                               data=self.clock_to_track[o_name],
                               compression='gzip', compression_opts=4,
                               dtype='float32')

        # Store all what_to_track variables
        for o_name in self.what_to_track:
            if self.log_save_counter >= 1:
                if h5f.get(self.seed_id + "/stats/" + o_name):
                    del h5f[self.seed_id + "/stats/" + o_name]
            data_to_store = self.stats_to_track[o_name].to_numpy()
            if type(data_to_store[0]) == np.ndarray:
                data_to_store = np.stack(data_to_store)
            h5f.create_dataset(name=self.seed_id + "/stats/" + o_name,
                               data=data_to_store,
                               compression='gzip', compression_opts=4,
                               dtype='float32')

        h5f.flush()
        h5f.close()

        # Tick the log save counter
        self.log_save_counter += 1

    def save_model(self, model):
        """ Save current state of the model as a checkpoint - torch! """
        # CASE 1: SIMPLE STORAGE OF MOST RECENTLY LOGGED MODEL STATE
        if self.model_type == "torch":
            # Torch model case - save model state dict as .pt checkpoint
            self.store_torch_model(self.final_model_save_fname, model)
        elif self.model_type in ["jax", "sklearn"]:
            # JAX/sklearn save parameter dict/model as dictionary
            self.store_pkl_model(self.final_model_save_fname, model)
        else:
            raise ValueError("Provide valid model_type [torch, jax, sklearn].")

        # CASE 2: SEPARATE STORAGE OF EVERY K-TH LOGGED MODEL STATE
        if self.save_every_k_ckpt is not None:
            if self.log_save_counter % self.save_every_k_ckpt == 0:
                if self.model_type == "torch":
                    ckpt_path = (self.ckpt_model_save_fname + "_" +
                                 str(self.model_save_counter) + ".pt")
                    self.store_torch_model(ckpt_path, model)
                elif self.model_type in ["jax", "sklearn"]:
                    ckpt_path = (self.ckpt_model_save_fname + "_" +
                                 str(self.model_save_counter) + ".pkl")
                    self.store_pkl_model(ckpt_path, model)
                self.model_save_counter += 1

        # TODO: CASE 3: STORE TOP-K MODEL STATES BY SOME SCORE

    def store_torch_model(self, path_to_store, model):
        """ Store a torch checkpoint for a model. """
        try:
            import torch
        except ModuleNotFoundError as err:
            raise ModuleNotFoundError(f"{err}. You need to install "
                                      "`torch` if you want to save a model "
                                      "checkpoint.")
        # Update the saved weights in a single file!
        torch.save(model.state_dict(), path_to_store)

    def store_pkl_model(self, path_to_store, model):
        """ Store a pickle object for a JAX param dict/sklearn model. """
        with open(path_to_store, 'wb') as fid:
            pickle.dump(model, fid)
