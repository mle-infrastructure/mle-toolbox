from .report import ReportGenerator
from .protocol import load_local_protocol_db


def user_generate_reports():
    """ Interface for user-defined generation of experiment report. """
    # TODO: use command `report-experiment` for the following steps
    # 1. Load db and show most recent experiments [give option for more]
    # 2. Let user choose an e_id.
    # 3. Create db using ReportGenerator
    raise NotImplementedError


def auto_generate_reports(e_id):
    """ Default auto-generation of reports for latest experiment. """
    # Load in experiment protocol db
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()

    # Creater 'reporter' instance aka Karla Kolumna - and write
    reporter = ReportGenerator(e_id, db)
    reporter.generate_reports()
    return reporter
