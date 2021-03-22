import numpy as np
import pandas as pd
import os
import shutil
import time
import datetime
import h5py
from typing import Union, List
from .general import save_pkl_object


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
        seed_id (str): seed id to distinguish logs with
        overwrite_experiment_dir (bool): delete old log file/tboard dir
        ======= VERBOSITY/TBOARD LOGGING
        print_every_k_updates (int): after how many log updates - verbose
        use_tboard (bool): whether to log to tensorboard
        tboard_fname (str): base name of tensorboard
        ======= MODEL STORAGE
        model_type (str): ["torch", "jax", "sklearn"] - tboard/storage
        ckpt_time_to_track (str): Variable name/score key to save
        save_every_k_ckpt (int): save every other checkpoint
        save_top_k_ckpt (int): save top k performing checkpoints
        top_k_metric_name (str): Variable name/score key to save
        top_k_minimize_metric (str): Boolean for min/max score in top k logging
    """
    def __init__(self,
                 time_to_track: List[str],
                 what_to_track: List[str],
                 time_to_print: List[str],
                 what_to_print: List[str],
                 config_fname: str,
                 experiment_dir: str = "/",
                 seed_id: Union[str, None] = None,
                 overwrite_experiment_dir: bool = False,
                 use_tboard: bool = False,
                 tboard_fname: Union[str, None] = None,
                 print_every_k_updates: Union[int, None] = None,
                 model_type: str = "no-model-type-provided",
                 ckpt_time_to_track: Union[str, None] = None,
                 save_every_k_ckpt: Union[int, None] = None,
                 save_top_k_ckpt: Union[int, None] = None,
                 top_k_metric_name: Union[str, None] = None,
                 top_k_minimize_metric: Union[bool, None] = None):
        # Initialize counters of log - log, model, figures
        self.log_update_counter = 0
        self.log_save_counter = 0
        self.model_save_counter = 0
        self.fig_save_counter = 0
        self.fig_storage_paths = []
        self.print_every_k_updates = print_every_k_updates

        # MODEL LOGGING SETUP: Type of model/every k-th ckpt/top k ckpt
        self.model_type = model_type
        self.ckpt_time_to_track = ckpt_time_to_track
        self.save_every_k_ckpt = save_every_k_ckpt
        self.save_top_k_ckpt = save_top_k_ckpt
        self.top_k_metric_name = top_k_metric_name
        self.top_k_minimize_metric = top_k_minimize_metric

        # Initialize lists for top k scores and to track storage times
        if self.save_every_k_ckpt is not None:
            self.every_k_storage_time = []
        if self.save_top_k_ckpt is not None:
            self.top_k_performance = []
            self.top_k_storage_time = []

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

        # Keep the seed id around
        self.seed_id = seed_id

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
        if not os.path.exists(os.path.join(self.experiment_dir, "models/final/")):
            try: os.mkdir(os.path.join(self.experiment_dir, "models/final/"))
            except: pass
        if self.save_every_k_ckpt is not None:
            if not os.path.exists(os.path.join(self.experiment_dir, "models/every_k/")):
                try: os.mkdir(os.path.join(self.experiment_dir, "models/every_k/"))
                except: pass
        if self.save_top_k_ckpt is not None:
            if not os.path.exists(os.path.join(self.experiment_dir, "models/top_k/")):
                try: os.mkdir(os.path.join(self.experiment_dir, "models/top_k/"))
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
        self.final_model_save_fname = (self.experiment_dir + "models/final/" +
                                       timestr + base_str + "_" + seed_id)
        if self.save_every_k_ckpt is not None:
            self.every_k_ckpt_list = []
            self.every_k_model_save_fname = (self.experiment_dir + "models/every_k/" +
                                             timestr + base_str + "_" + seed_id
                                             + "_k_")
        if self.save_top_k_ckpt is not None:
            self.top_k_ckpt_list = []
            self.top_k_model_save_fname = (self.experiment_dir + "models/top_k/" +
                                           timestr + base_str + "_" + seed_id
                                           + "_top_")

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

        # Initialize tensorboard logger/summary writer
        if tboard_fname is not None and use_tboard:
            try:
                from torch.utils.tensorboard import SummaryWriter
            except ModuleNotFoundError as err:
                raise ModuleNotFoundError(f"{err}. You need to install "
                                          "`torch` if you want that "
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
            # Save the most recent model checkpoint
            if model is not None:
                self.save_model(model)
            self.save_log()

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
            if self.model_type == "torch":
                for name, param in model.named_parameters():
                    self.writer.add_histogram('weights/' + name,
                                              param.clone().cpu().data.numpy(),
                                              clock_tick[0])
                    self.writer.add_histogram('gradients/' + name,
                                        param.grad.clone().cpu().data.numpy(),
                                        clock_tick[0])
            elif self.model_type == "jax":
                # Try to add parameters from nested dict first - then simple
                # Gradients would have to be parsed separately...
                for l in model.keys():
                    try:
                        for w in model[l].keys():
                            self.writer.add_histogram('weights/' + l + '/' + w,
                                                       np.array(model[l][w]),
                                                       clock_tick[0])
                    except:
                        self.writer.add_histogram('weights/' + l,
                                                  np.array(model[l]),
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
                compression='gzip', compression_opts=4, dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/log_paths",
                        data=[self.log_save_fname.encode("ascii", "ignore")],
                        compression='gzip', compression_opts=4, dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/experiment_dir",
                        data=[self.experiment_dir.encode("ascii", "ignore")],
                        compression='gzip', compression_opts=4, dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/config_fname",
                        data=[self.config_copy.encode("ascii", "ignore")],
                        compression='gzip', compression_opts=4, dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/eval_id",
                        data=[self.base_str.encode("ascii", "ignore")],
                        compression='gzip', compression_opts=4, dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/model_type",
                        data=[self.model_type.encode("ascii", "ignore")],
                        compression='gzip', compression_opts=4, dtype='S200')

            if self.save_top_k_ckpt or self.save_every_k_ckpt:
                h5f.create_dataset(
                    name=self.seed_id + "/meta/ckpt_time_to_track",
                    data=[self.ckpt_time_to_track.encode("ascii", "ignore")],
                    compression='gzip', compression_opts=4, dtype='S200')

            if self.save_top_k_ckpt:
                h5f.create_dataset(
                    name=self.seed_id + "/meta/top_k_metric_name",
                    data=[self.top_k_metric_name.encode("ascii", "ignore")],
                    compression='gzip', compression_opts=4, dtype='S200')

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

        # Store data on stored checkpoints - stored every k updates
        if self.save_every_k_ckpt is not None:
            if self.log_save_counter >= 1:
                for o_name in ["every_k_storage_time", "every_k_ckpt_list"]:
                    if h5f.get(self.seed_id + "/meta/" + o_name):
                        del h5f[self.seed_id + "/meta/" + o_name]
            h5f.create_dataset(name=self.seed_id + "/meta/every_k_storage_time",
                               data=np.array(self.every_k_storage_time),
                               compression='gzip', compression_opts=4,
                               dtype='float32')
            h5f.create_dataset(name=self.seed_id + "/meta/every_k_ckpt_list",
                               data=[t.encode("ascii", "ignore") for t
                                     in self.every_k_ckpt_list],
                               compression='gzip', compression_opts=4,
                               dtype='S200')

        #  Store data on stored checkpoints - stored top k ckpt
        if self.save_top_k_ckpt is not None:
            if self.log_save_counter >= 1:
                for o_name in ["top_k_storage_time", "top_k_ckpt_list",
                               "top_k_performance"]:
                    if h5f.get(self.seed_id + "/meta/" + o_name):
                        del h5f[self.seed_id + "/meta/" + o_name]
            h5f.create_dataset(name=self.seed_id + "/meta/top_k_storage_time",
                               data=np.array(self.top_k_storage_time),
                               compression='gzip', compression_opts=4,
                               dtype='float32')
            h5f.create_dataset(name=self.seed_id + "/meta/top_k_ckpt_list",
                               data=[t.encode("ascii", "ignore") for t
                                     in self.top_k_ckpt_list],
                               compression='gzip', compression_opts=4,
                               dtype='S200')
            h5f.create_dataset(name=self.seed_id + "/meta/top_k_performance",
                               data=np.array(self.top_k_performance),
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
            save_pkl_object(model, self.final_model_save_fname)
        else:
            raise ValueError("Provide valid model_type [torch, jax, sklearn].")

        # CASE 2: SEPARATE STORAGE OF EVERY K-TH LOGGED MODEL STATE
        if self.save_every_k_ckpt is not None:
            if self.log_save_counter % self.save_every_k_ckpt == 0:
                if self.model_type == "torch":
                    ckpt_path = (self.every_k_model_save_fname +
                                 str(self.model_save_counter) + ".pt")
                    self.store_torch_model(ckpt_path, model)
                elif self.model_type in ["jax", "sklearn"]:
                    ckpt_path = (self.every_k_model_save_fname +
                                 str(self.model_save_counter) + ".pkl")
                    save_pkl_object(model, ckpt_path)
                # Update model save count & time point of storage
                self.model_save_counter += 1
                time = self.clock_to_track[self.ckpt_time_to_track].to_numpy()[-1]
                self.every_k_storage_time.append(time)
                self.every_k_ckpt_list.append(ckpt_path)

        # CASE 3: STORE TOP-K MODEL STATES BY SOME SCORE
        if self.save_top_k_ckpt is not None:
            updated_top_k = False
            score = self.stats_to_track[self.top_k_metric_name].to_numpy()[-1]
            time = self.clock_to_track[self.ckpt_time_to_track].to_numpy()[-1]
            # Fill up empty top k slots
            if len(self.top_k_performance) < self.save_top_k_ckpt:
                if self.model_type == "torch":
                    ckpt_path = (self.top_k_model_save_fname +
                                 str(len(self.top_k_performance)) + ".pt")
                    self.store_torch_model(ckpt_path, model)
                elif self.model_type in ["jax", "sklearn"]:
                    ckpt_path = (self.top_k_model_save_fname +
                                 str(len(self.top_k_performance)) + ".pkl")
                    save_pkl_object(model, ckpt_path)
                updated_top_k = True
                self.top_k_performance.append(score)
                self.top_k_storage_time.append(time)
                self.top_k_ckpt_list.append(ckpt_path)

            # If minimize = replace worst performing model (max score)
            if (self.top_k_minimize_metric and
                max(self.top_k_performance) > score and not updated_top_k):
                id_to_replace = np.argmax(self.top_k_performance)
                self.top_k_performance[id_to_replace] = score
                self.top_k_storage_time[id_to_replace] = time
                if self.model_type == "torch":
                    ckpt_path = (self.top_k_model_save_fname +
                                 str(id_to_replace) + ".pt")
                    self.store_torch_model(ckpt_path, model)
                elif self.model_type in ["jax", "sklearn"]:
                    ckpt_path = (self.top_k_model_save_fname +
                                 str(id_to_replace) + ".pkl")
                    save_pkl_object(model, ckpt_path)
                updated_top_k = True

            # If minimize = replace worst performing model (max score)
            if (not self.top_k_minimize_metric and
                min(self.top_k_performance) > score and not updated_top_k):
                id_to_replace = np.argmin(self.top_k_performance)
                self.top_k_performance[id_to_replace] = score
                self.top_k_storage_time[id_to_replace] = (
                    self.clock_to_track[
                        self.ckpt_time_to_track].to_numpy()[-1])
                if self.model_type == "torch":
                    ckpt_path = (self.top_k_model_save_fname + "_top_" +
                                 str(id_to_replace) + ".pt")
                    self.store_torch_model(ckpt_path, model)
                elif self.model_type in ["jax", "sklearn"]:
                    ckpt_path = (self.top_k_model_save_fname + "_top_" +
                                 str(id_to_replace) + ".pkl")
                    save_pkl_object(model, ckpt_path)
                updated_top_k = True

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

    def save_plot(self, fig, fname_ext=".png"):
        """ Store a figure in a experiment_id/figures directory. """
        # Create new directory to store figures - if it doesn't exist yet
        figures_dir = os.path.join(self.experiment_dir, "figures/")
        if not os.path.exists(figures_dir):
            try: os.makedirs(figures_dir)
            except: pass

        # Tick up counter, save figure, store new path to figure
        self.fig_save_counter += 1
        figure_fname = os.path.join(figures_dir,
                                    "fig_" + str(self.fig_save_counter) +
                                    "seed_" + str(self.seed_id)
                                    + fname_ext)
        fig.savefig(figure_fname, dpi=300)
        self.fig_storage_paths.append(figure_fname)

        # Store figure paths if any where created
        h5f = h5py.File(self.log_save_fname, 'a')
        if self.fig_save_counter > 1:
            if h5f.get(self.seed_id + "/meta/fig_storage_paths"):
                del h5f[self.seed_id + "/meta/fig_storage_paths"]
        h5f.create_dataset(name=self.seed_id + "/meta/fig_storage_paths",
                           data=[t.encode("ascii", "ignore") for t
                                 in self.fig_storage_paths],
                           compression='gzip', compression_opts=4,
                           dtype='S200')
        h5f.flush()
        h5f.close()

    def save_to_extra_dir(self, obj, fname):
        """ Helper fct. to save object (dict/etc.) as .pkl in exp. subdir. """
        extra_dir = os.path.join(self.experiment_dir, "extra/")
        path_to_store = os.path.join(extra_dir, fname)
        # Create a new empty directory for the experiment
        if not os.path.exists(extra_dir):
            try: os.makedirs(extra_dir)
            except: pass
        save_pkl_object(obj, path_to_store)
