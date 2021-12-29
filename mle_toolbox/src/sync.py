from mle_toolbox import mle_config
from mle_toolbox.utils import print_framed
from mle_monitor.utils import get_gcloud_zip
from mle_monitor import MLEProtocol


def sync():
    """Download experiments in GCS bucket onto drive + delete remote files."""
    # Download the current state of the protocol db and load it in
    protocol_db = MLEProtocol(mle_config.general.local_protocol_fname, mle_config.gcp)
    for i, e_id in enumerate(protocol_db.experiment_ids):
        # Download + delete all stored experiments
        try:
            stored_in_gcloud = protocol_db.get(e_id, "stored_in_gcloud")
            not_retrieved_yet = not protocol_db.get(e_id, "retrieve_results")
        except Exception:
            stored_in_gcloud = False
        # Pull either from remote machine or gcloud bucket
        if stored_in_gcloud:
            # Pull only if you haven't retrieved before
            # TODO: Make this optional - ask user if want to retrieve again
            if not_retrieved_yet:
                print_framed(f"RETRIEVE E-ID {e_id}")
                _ = get_gcloud_zip(protocol_db, e_id)
                # print_framed(f"DELETE E-ID {e_id}")
                # delete_gcs_dir(gcloud_hash_fname)
                print_framed(f"COMPLETED E-ID {e_id}")

            # TODO: Update protocol 'retrieved' status
