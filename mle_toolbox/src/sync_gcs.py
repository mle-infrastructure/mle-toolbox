from mle_toolbox.utils import print_framed
from mle_toolbox.protocol import load_local_protocol_db
from mle_toolbox.remote.gcloud_transfer import (get_gcloud_db,
                                                send_gcloud_db,
                                                get_gcloud_zip_experiment,
                                                delete_gcs_directory)


def sync_gcs():
    """ Download experiments in GCS bucket onto drive + delete remote files. """
    # Download the current state of the protocol db and load it in
    get_gcloud_db()
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    for i, e_id in enumerate(all_experiment_ids):
        # Download + delete all stored experiments
        try:
            stored_in_gcloud = db.dget(e_id, "stored_in_gcloud")
            not_retrieved_yet = not db.dget(e_id, "retrieve_results")
        except:
            stored_in_gcloud = False
        # Pull either from remote machine or gcloud bucket
        if stored_in_gcloud:
            # Pull only if you haven't retrieved before
            # TODO: Make this optional - ask user if want to retrieve again
            if not_retrieved_yet:
                print_framed(f'RETRIEVE E-ID {e_id}')
                gcloud_hash_fname = get_gcloud_zip_experiment(
                                            db, e_id, all_experiment_ids
                                                              )
                print_framed(f'DELETE E-ID {e_id}')
                delete_gcs_directory(gcloud_hash_fname)
                print_framed(f'COMPLETED E-ID {e_id}')
    send_gcloud_db()
