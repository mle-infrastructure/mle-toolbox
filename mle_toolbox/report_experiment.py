from datetime import datetime

from .report import ReportGenerator
from .utils import load_mle_toolbox_config
from .protocol import protocol_summary, load_local_protocol_db
from .remote.gcloud_transfer import get_gcloud_db


def main():
    """ Interface for user-defined generation of experiment report. """
    # 1. Load db and show most recent experiments [give option for more]
    # 2. Let user choose an e_id.
    # 3. Create db using ReportGenerator
    # Load cluster config
    cc = load_mle_toolbox_config()
    # Get most recent/up-to-date experiment DB from Google Cloud Storage
    if cc.general.use_gcloud_protocol_sync:
        accessed_remote_db = get_gcloud_db()
    else:
        accessed_remote_db = False
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    if accessed_remote_db:
        print(time_t,
              "Successfully pulled latest experiment protocol from gcloud.")
    else:
        print(time_t, "Careful - you are using the local experiment protocol.")
    # Load in the experiment protocol DB
    db, all_experiment_ids, _ = load_local_protocol_db()

    protocol_summary(tail=10)
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    experiment_id = input(time_t + " Which experiment do you " +
                          "want to retrieve? [E-ID/N]:  ")

    while True:
        if experiment_id[:5] != "e-id-":
            experiment_id = "e-id-" + experiment_id

        if experiment_id not in all_experiment_ids:
            print(time_t, "The experiment you try to retrieve does not exist")
            experiment_id = input(time_t + " Which experiment do you " +
                                  "want to retrieve?")
        else:
            break

    # Create 'reporter' instance aka Karla Kolumna - and write
    reporter = auto_generate_reports(experiment_id)
    return reporter


def auto_generate_reports(e_id):
    """ Default auto-generation of reports for latest experiment. """
    # Load in experiment protocol db
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()

    # Create 'reporter' instance aka Karla Kolumna - and write
    reporter = ReportGenerator(e_id, db)
    reporter.generate_reports()
    return reporter
