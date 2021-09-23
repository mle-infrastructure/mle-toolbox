import os
import pandas as pd
from dotmap import DotMap
import matplotlib.pyplot as plt
from mle_toolbox.utils import load_pkl_object
from mle_logging import load_log


def load_pbt_log(pbt_dir: str, path_start: str = ""):
    pbt_log_path = os.path.join(path_start, pbt_dir, "pbt_log.pkl")
    reload_log = load_pkl_object(pbt_log_path)
    pbt_log = PBTLog(reload_log["performance"],
                     reload_log["trajectory"],
                     path_start)
    return pbt_log


class PBTLog(object):
    def __init__(self,
                 perf_log: pd.DataFrame,
                 copy_log: pd.DataFrame,
                 path_start: str = ""):
        """PBT Log Wrapper for easy results retrieval"""
        self.perf_log = perf_log.sort_values(["pbt_step_id", "worker_id"])
        self.copy_log = copy_log
        self.path_start = path_start
        self.worker_ids = self.perf_log.worker_id.unique()
        self.step_ids = self.perf_log.pbt_step_id.unique()
        self.worker_logs = self.load_worker_logs()

    def load_worker_logs(self):
        """Load individual sublogs of workers at different steps."""
        worker_logs = DotMap()
        for worker_id in self.worker_ids:
            w_logs = {}
            for step_id in self.step_ids:
                w_t_temp = self.perf_log[
                    (self.perf_log["worker_id"] == worker_id)
                    & (self.perf_log["pbt_step_id"] == step_id)]
                w_t_log = load_log(self.path_start + w_t_temp.log_path.iloc[0])
                w_logs["step_" + str(step_id)] = w_t_log
            worker_logs["worker_" + str(worker_id)] = DotMap(w_logs)
        return worker_logs

    def plot_worker_perf(self):
        """1D Learning Curve of Individual Workers."""
        fig, ax = plt.subplots(figsize=(7,5))
        for worker_id in self.worker_ids:
            ax.plot(self.step_ids,
                    self.perf_log[self.perf_log.worker_id == worker_id].objective)
        ax.set_xlabel("PBT Steps")
        ax.set_ylabel("Objective")
        ax.set_title(f"PBT Log - {len(self.worker_ids)} Workers"\
                     f" - {len(self.worker_ids)} PBT Steps")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
