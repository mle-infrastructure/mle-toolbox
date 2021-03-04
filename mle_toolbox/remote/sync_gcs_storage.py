from ..utils import print_framed
from ..protocol import load_local_protocol_db
from .gcloud_transfer import (get_gcloud_db, send_gcloud_db,
                              get_gcloud_zip_experiment,
                              delete_gcs_directory)


def main():
    """ Download experiments in GCS bucket onto drive + delete remote files. """
    get_gcloud_db()
    db, all_experiment_ids, last_experiment_id = load_local_protocol_db()
    print(db.getall())
    print(db.get("e-id-306"))
    for i, e_id in enumerate(all_experiment_ids):
        try:
            stored_in_gcloud = db.dget(e_id, "stored_in_gcloud")
        except:
            stored_in_gcloud = False
        # Pull either from remote machine or gcloud bucket
        if stored_in_gcloud:
            print_framed(f'RETRIEVE E-ID {e_id}')
            get_gcloud_zip_experiment(db, e_id,
                                      all_experiment_ids)
            print_framed(f'COMPLETED E-ID {e_id}')
    send_gcloud_db( )
