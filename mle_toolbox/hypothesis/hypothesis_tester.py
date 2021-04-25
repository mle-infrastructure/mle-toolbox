import numpy as np
from statsmodels.stats.weightstats import ztest
from statsmodels.stats.multitest import multipletests


class HypothesisTester(object):
    """
    Helper for Testing Hypotheses & Correcting for Multiple Testing and FDR.
    TODO: Add more than just z-test.
    """
    def __init__(self, meta_log):
        self.meta_log = meta_log
        self.eval_ids = self.meta_log.eval_ids
        self.num_evals = len(meta_log)
        self.correct_methods = ['bonferroni', 'sidak', 'holm-sidak', 'holm',
                                'simes-hochberg', 'hommel', 'fdr_bh',
                                'fdr_tsbh', 'fdr_tsbky']

    def run_pairwise(self, metric_name: str):
        """
        Run pairwise test of runs against each other. One-sided z-test
        $H_0: \mathbb{E}_t[\mathcal{L}^A(t) - \mathcal{L}^B(t)] = 0$ vs.
        $H_1: \mathbb{E}_t[\mathcal{L}^A(t) - \mathcal{L}^B(t)] < 0$
        So we are testing whether we can reject that run A is not better B.
        """
        self.p_vals = np.zeros((self.num_evals, self.num_evals))
        # TODO: Parallelize/vectorize this?!
        for i in range(self.num_evals):
            for j in range(self.num_evals):
                # One sided z-test = i - j is non-zero: Rejection (smaller than)
                z_stat, p_val = ztest(
                    self.meta_log[self.eval_ids[i]].stats[metric_name].mean -
                    self.meta_log[self.eval_ids[j]].stats[metric_name].mean,
                    alternative='smaller')
                self.p_vals[self.num_evals - i - 1, j] = p_val

    def run_corrections(self):
        """
        Run set of corrections for all rows separately.
            bonferroni : one-step correction
            sidak : one-step correction
            holm-sidak : step down method using Sidak adjustments
            holm : step-down method using Bonferroni adjustments
            simes-hochberg : step-up method (independent)
            hommel : closed method based on Simes tests (non-negative)
            fdr_bh : Benjamini/Hochberg (non-negative)
            fdr_tsbh : two stage fdr correction (non-negative)
            fdr_tsbky : two stage fdr correction (non-negative)
        """
        self.corrected_p_vals = {}
        for c_name in self.correct_methods:
            self.corrected_p_vals[c_name] = self.single_correction(c_name)

    def single_correction(self, correction_name: str):
        """ Run a single correction for all rows in p_vals array. """
        p_vals_temp = np.flip(self.p_vals, axis=0)
        assert correction_name in self.correct_methods
        corrected_p_vals = np.zeros((self.num_evals, self.num_evals - 1))
        # Remove diagonal (test agains self - replace with 1)
        clean_p_val = p_vals_temp[~np.eye(p_vals_temp.shape[0],dtype=bool)]
        clean_p_val = clean_p_val.reshape(p_vals_temp.shape[0], -1)
        diag_elem = p_vals_temp.diagonal()
        for eval_run in range(self.num_evals):
            _, p_correct, _, _ = multipletests(clean_p_val[eval_run],
                                               method=correction_name)
            corrected_p_vals[eval_run] = p_correct
        # Readd diagonal column
        d = corrected_p_vals.shape[0]
        assert corrected_p_vals.shape[1] == d - 1
        matrix_new = np.ndarray((d, d+1))
        matrix_new[:,0] = 1
        matrix_new[:-1, 1:] = corrected_p_vals.reshape((d-1, d))
        matrix_new = matrix_new.reshape(-1)[:-d].reshape(d,d)
        return np.flip(matrix_new, axis=0)

    def plot(self, corrected: bool=False, method: str="bonferroni"):
        """ Helper plot function for p-values (corrected with method). """
        from mle_toolbox.visualize import plot_2D_heatmap
        if corrected:
            p_vals_to_plot = self.corrected_p_vals[method]
        else:
            p_vals_to_plot = self.p_vals

        plot_title = (r"$H_0: \mathbb{E}_t[\mathcal{L}^A - \mathcal{L}^B] = 0$"
                      + r" vs. " +
                      " $H_1: \mathbb{E}_t[\mathcal{L}^A - \mathcal{L}^B] < 0$")
        fig, ax = plot_2D_heatmap(self.eval_ids, self.eval_ids, p_vals_to_plot,
                                  min_heat=0.0, max_heat=0.15,
                                  title = plot_title,
                                  xy_labels=["Run A", "Run B"],
                                  variable_name="Corrected P-Values",
                                  figsize=(12, 10))
