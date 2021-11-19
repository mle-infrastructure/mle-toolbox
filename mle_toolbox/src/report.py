from typing import Union
from mle_toolbox.report import ReportGenerator
from mle_toolbox import mle_config
from mle_monitor import MLEProtocol


def report(cmd_args):
    """Interface for user-defined generation of experiment report."""
    protocol_db = MLEProtocol(mle_config.general.local_protocol_fname, mle_config.gcp)

    if not cmd_args.use_last_id:
        # 0. Get command line input for experiment id
        experiment_id = cmd_args.experiment_id
        # 1. Load db and show recent experiments + let user choose an e_id.
        if experiment_id == "no-id-given":
            protocol_db.summary(tail=10, verbose=True)
            experiment_id = protocol_db.ask_for_e_id("report")
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
        e_id = str(protocol_db.last_experiment_id)
    else:
        e_id = str(e_id)
    protocol_data = protocol_db.get(str(e_id))
    reporter = ReportGenerator(str(e_id), protocol_data, logger, pdf_gen)
    reporter.generate_reports()
    return reporter
