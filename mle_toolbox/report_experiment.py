from datetime import datetime
from .report import ReportGenerator
from .src.prepare_experiment import ask_for_experiment_id


def main():
    """ Interface for user-defined generation of experiment report. """
    # 1. Load db and show recent experiments + let user choose an e_id.
    experiment_id, _, _, _ = ask_for_experiment_id()
    # 2. Create 'reporter' instance and write reports
    reporter = auto_generate_reports(experiment_id)


def auto_generate_reports(e_id):
    """ Default auto-generation of reports for latest experiment. """
    # Load in experiment protocol db
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    # Create 'reporter' instance aka Karla Kolumna - and write
    reporter = ReportGenerator(e_id, db)
    reporter.generate_reports()
    return reporter
