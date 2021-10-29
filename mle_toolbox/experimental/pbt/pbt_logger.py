from ..utils import save_pkl_object
import math
import os
import numpy as np
import pandas as pd
from typing import Tuple
from mle_logging import load_log


class PBT_Logger(object):
    def __init__(
        self,
        pbt_log_fname: str,
        experiment_dir: str,
        eval_metric: str,
        max_objective: bool,
        num_population_members: int,
    ):
        """Logging Class for PBT (Jaderberg et al. 17)."""
        self.pbt_log_fname = pbt_log_fname
        self.pbt_df = pd.DataFrame()
        self.trajectory_df = pd.DataFrame()
        self.experiment_dir = experiment_dir
        self.eval_metric = eval_metric
        self.max_objective = max_objective
        self.num_population_members = num_population_members

    def update_log(self, worker_log: dict, save: bool = True) -> None:
        """Update the performance log of the PBT search."""
        if len(self.pbt_df) == 0:
            self.pbt_df = self.pbt_df.append(
                pd.DataFrame([worker_log]), ignore_index=True
            )
        else:
            df_worker_pbt = self.pbt_df[
                (self.pbt_df.worker_id == worker_log["worker_id"])
                & (self.pbt_df.pbt_step_id == worker_log["pbt_step_id"])
            ]
            if len(df_worker_pbt) == 1:
                self.pbt_df.iloc[df_worker_pbt.index] = pd.DataFrame([worker_log])
            else:
                self.pbt_df = self.pbt_df.append(
                    pd.DataFrame([worker_log]), ignore_index=True
                )
        if save:
            self.save_log()

    def update_trajectory(self, trajectory_log: dict, save: bool = True) -> None:
        """Update the trajectory log of the PBT search."""
        self.trajectory_df = self.trajectory_df.append(
            pd.DataFrame([trajectory_log]), ignore_index=True
        )
        if save:
            self.save_log()

    def save_log(self):
        """Save the trace/log of the PBT."""
        pbt_data_log = {"performance": self.pbt_df, "trajectory": self.trajectory_df}
        save_pkl_object(pbt_data_log, self.pbt_log_fname)

    def get_most_recent_data(self) -> pd.DataFrame:
        """Subselect most recent data from the log."""
        recent = self.pbt_df.loc[
            self.pbt_df.reset_index().groupby(["worker_id"])["pbt_step_id"].idxmax()
        ]
        return recent

    def get_worker_data(self, worker_id: int, pbt_step_id: int, hyperparams: dict):
        """Get data for worker in pbt_step."""
        # Get path to experiment storage directory
        run_id = "worker_" + str(worker_id) + "_step_" + str(pbt_step_id)
        subdirs = [f.path for f in os.scandir(self.experiment_dir) if f.is_dir()]

        try:
            exp_dir = [f for f in subdirs if f.endswith(run_id)][0]
        except Exception as e:
            print(e, subdirs)
            exp_dir = ""

        log_dir = os.path.join(exp_dir, "logs")
        model_dir = os.path.join(exp_dir, "models", "final")

        # Load performance log of worker
        try:
            log_files = [
                os.path.join(log_dir, f)
                for f in os.listdir(log_dir)
                if (os.path.isfile(os.path.join(log_dir, f)) and f.endswith(".hdf5"))
            ]
        except Exception as e:
            print(e, exp_dir)
            log_files = []

        if len(log_files) > 0:
            log_path = log_files[0]
            # A bit awkward - try loading until no blocking occurs
            os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"
            while True:
                try:
                    perf_log = load_log(exp_dir)
                    break
                except Exception as e:
                    print(e, log_path)
                    continue
            perf = perf_log.stats[self.eval_metric][-1]
            num_updates = perf_log["time"]["num_updates"][-1]
        else:
            log_path = None
            perf = -np.inf if self.max_objective else np.inf
            num_updates = 0

        # Get network checkpoint filename
        model_suffixes = (".pt", ".npy", ".pkl")
        try:
            model_files = [
                os.path.join(model_dir, f)
                for f in os.listdir(model_dir)
                if (
                    os.path.isfile(os.path.join(model_dir, f))
                    and f.endswith(model_suffixes)
                )
            ]
        except Exception:
            model_files = []

        if len(model_files) > 0:
            model_ckpt = model_files[0]
        else:
            model_ckpt = None

        worker_log = {
            "worker_id": worker_id,
            "pbt_step_id": pbt_step_id,
            "num_updates": num_updates,
            "log_path": log_path,
            "model_ckpt": model_ckpt,
            self.eval_metric: perf,
            "hyperparams": hyperparams,
        }
        return worker_log

    def get_truncation_population(
        self, most_recent_df, truncation_percent
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Get top and bottom of performance distribution."""
        top_df, bottom_df = get_top_and_bottom(
            most_recent_df, truncation_percent, self.eval_metric, self.max_objective
        )
        return top_df, bottom_df


def get_top_and_bottom(
    df: pd.DataFrame, truncation_percent: float, eval_metric: str, max_objective: bool
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Get top and bottom of performance distribution."""
    num_population_members = df.shape[0]
    n_rows = math.ceil(num_population_members * truncation_percent)
    if max_objective:
        top_df = df.nlargest(n_rows, eval_metric)
        bottom_df = df.nsmallest(n_rows, eval_metric)
    else:
        top_df = df.nsmallest(n_rows, eval_metric)
        bottom_df = df.nlargest(n_rows, eval_metric)
    return top_df, bottom_df
