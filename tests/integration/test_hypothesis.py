import os
from mle_toolbox import load_result_logs
from mle_toolbox.experimental.hypothesis import HypothesisTester


def test_corrected_pairwise():
    meta_log, hyper_log = load_result_logs("tests/unit/fixtures/experiment_1")
    hypo_tester = HypothesisTester(meta_log)
    hypo_tester.run_pairwise("integral")
    hypo_tester.run_corrections()

    for correct_m in [
        "bonferroni",
        "sidak",
        "holm-sidak",
        "holm",
        "simes-hochberg",
        "hommel",
        "fdr_bh",
        "fdr_tsbh",
        "fdr_tsbky",
    ]:
        assert hypo_tester.corrected_p_vals[correct_m].shape == (
            len(meta_log.eval_ids),
            len(meta_log.eval_ids),
        )


def test_plot_p_values():
    meta_log, hyper_log = load_result_logs("tests/unit/fixtures/experiment_1")
    hypo_tester = HypothesisTester(meta_log)
    hypo_tester.run_pairwise("integral")
    hypo_tester.run_corrections()
    hypo_tester.plot(corrected=True, method="bonferroni", fname="bonferroni_p_vals.png")
    assert os.path.exists("bonferroni_p_vals.png")
    os.remove("bonferroni_p_vals.png")
