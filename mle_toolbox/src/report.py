from typing import Union
from mle_toolbox.report import ReportGenerator
from mle_toolbox.launch.prepare_experiment import ask_for_experiment_id
from mle_toolbox import mle_config
from mle_monitor import MLEProtocol


def report(cmd_args):
    """Interface for user-defined generation of experiment report."""
    if mle_config.general.use_gcloud_protocol_sync:
        from ..remote.gcloud_transfer import get_gcloud_db

        accessed_remote_db = get_gcloud_db()
        time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
        if accessed_remote_db:
            print(time_t, "Successfully pulled latest experiment protocol from gcloud.")
        else:
            print(time_t, "Careful - you are using local experiment protocol.")
    protocol_db = MLEProtocol(mle_config.general.local_protocol_fname)

    if not cmd_args.use_last_id:
        # 0. Get command line input for experiment id
        experiment_id = cmd_args.experiment_id
        # 1. Load db and show recent experiments + let user choose an e_id.
        if experiment_id == "no-id-given":
            experiment_id = ask_for_experiment_id(protocol_db)
        else:
            if experiment_id[:5] != "e-id-":
                experiment_id = "e-id-" + experiment_id
    else:
        experiment_id = None
    # 2. Create 'reporter' instance and write reports
    auto_generate_reports(experiment_id, protocol_db, pdf_gen=True)


def auto_generate_reports(
    e_id: Union[str, None], protocol_db: MLEProtocol, logger=None, pdf_gen: bool = False
):
    """Default auto-generation of reports for latest experiment."""
    # Create 'reporter' instance aka Karla Kolumna - and write
    if e_id is None:
        e_id = "e-id-" + str(protocol_db.last_experiment_id)
    protocol_data = protocol_db.get(e_id)
    reporter = ReportGenerator(e_id, protocol_data, logger, pdf_gen)
    reporter.generate_reports()
    return reporter
