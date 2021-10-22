from typing import Union
from mle_toolbox.report import ReportGenerator
from mle_toolbox.launch.prepare_experiment import ask_for_experiment_id
from mle_monitor import load_local_protocol_db


def report(cmd_args):
    """Interface for user-defined generation of experiment report."""
    if not cmd_args.use_last_id:
        # 0. Get command line input for experiment id
        experiment_id = cmd_args.experiment_id
        # 1. Load db and show recent experiments + let user choose an e_id.
        if experiment_id == "no-id-given":
            experiment_id, _, _, _ = ask_for_experiment_id()
        else:
            if experiment_id[:5] != "e-id-":
                experiment_id = "e-id-" + experiment_id
    else:
        experiment_id = None
    # 2. Create 'reporter' instance and write reports
    auto_generate_reports(experiment_id, pdf_gen=True)


def auto_generate_reports(e_id: Union[str, None], logger=None, pdf_gen: bool = False):
    """Default auto-generation of reports for latest experiment."""
    # Load in experiment protocol db
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    # Create 'reporter' instance aka Karla Kolumna - and write
    if e_id is None:
        e_id = "e-id-" + str(last_experiment_id)
    reporter = ReportGenerator(e_id, db, logger, pdf_gen)
    reporter.generate_reports()
    return reporter
