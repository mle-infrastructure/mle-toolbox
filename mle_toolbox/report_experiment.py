import argparse
from datetime import datetime
from .report import ReportGenerator
from .src.prepare_experiment import ask_for_experiment_id
from .protocol import load_local_protocol_db


def get_retrieve_args():
    """ Get inputs from cmd line """
    parser = argparse.ArgumentParser()
    parser.add_argument('-e_id', '--experiment_id', type=str,
                        default="no-id-given",
                        help ='Experiment ID')
    return parser.parse_args()


def main():
    """ Interface for user-defined generation of experiment report. """
    # 0. Get command line input for experiment id
    experiment_id = get_retrieve_args().experiment_id
    # 1. Load db and show recent experiments + let user choose an e_id.
    if experiment_id == "no-id-given":
        experiment_id, _, _, _ = ask_for_experiment_id()
    else:
        if experiment_id[:5] != "e-id-":
            experiment_id = "e-id-" + experiment_id
    # 2. Create 'reporter' instance and write reports
    reporter = auto_generate_reports(experiment_id)


def auto_generate_reports(e_id, logger=None, pdf_gen=False):
    """ Default auto-generation of reports for latest experiment. """
    # Load in experiment protocol db
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    # Create 'reporter' instance aka Karla Kolumna - and write
    reporter = ReportGenerator(e_id, db, logger, pdf_gen)
    reporter.generate_reports()
    return reporter
