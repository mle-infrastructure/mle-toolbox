import os
import glob
from os.path import expanduser
import logging
import zipfile
import shutil
from datetime import datetime
from typing import Union

from mle_toolbox import mle_config
from mle_monitor import MLEProtocol
from .ssh_manager import setup_proxy_server

try:
    from google.cloud import storage
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(
        f"{err}. You need to"
        "install `google-cloud-storage` to use "
        "the `mle_toolbox.remote.gcloud_transfer` module."
    )


# Set environment variable for gcloud credentials & proxy remote
setup_proxy_server()


def delete_gcs_dir(gcs_path: str, number_of_connect_tries: int = 5):
    """Delete a directory in a GCS bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(mle_config.gcp.project_name)
            bucket = client.get_bucket(mle_config.gcp.bucket_name, timeout=20)
        except Exception:
            logger.info(
                f"Attempt {i+1}/{number_of_connect_tries}"
                " - Failed sending to GCloud Storage"
            )

    # Delete all files in directory
    blobs = bucket.list_blobs(prefix=gcs_path)
    for blob in blobs:
        try:
            blob.delete()
        except Exception:
            pass


def upload_local_dir_to_gcs(
    local_path: str, gcs_path: str, number_of_connect_tries: int = 5
):
    """Send entire dir (recursively) to Google Cloud Storage Bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(mle_config.gcp.project_name)
            bucket = client.get_bucket(mle_config.gcp.bucket_name, timeout=20)
        except Exception:
            logger.info(
                f"Attempt {i+1}/{number_of_connect_tries}"
                " - Failed sending to GCloud Storage"
            )

    def upload_single_file(local_path, gcs_path, bucket):
        # Recursively upload the folder structure
        if os.path.isdir(local_path):
            for local_file in glob.glob(os.path.join(local_path, "**")):
                if not os.path.isfile(local_file):
                    upload_single_file(
                        local_file,
                        os.path.join(gcs_path, os.path.basename(local_file)),
                        bucket,
                    )
                else:
                    remote_path = os.path.join(
                        gcs_path, local_file[1 + len(local_path) :]
                    )
                    blob = bucket.blob(remote_path)
                    blob.upload_from_filename(local_file)
        # Only upload single file - e.g. zip compressed experiment
        else:
            remote_path = gcs_path
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_path)

    upload_single_file(local_path, gcs_path, bucket)


def download_gcs_dir(
    gcs_path: str, local_path: str = "", number_of_connect_tries: int = 5
):
    """Download entire dir (recursively) from Google Cloud Storage Bucket."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(mle_config.gcp.project_name)
            bucket = client.get_bucket(mle_config.gcp.bucket_name, timeout=20)
        except Exception:
            logger.info(
                f"Attempt {i+1}/{number_of_connect_tries}"
                f" - Failed sending to GCloud Storage"
            )

    blobs = bucket.list_blobs(prefix=gcs_path)  # Get list of files
    blobs = list(blobs)

    # Recursively download the folder structure
    if len(blobs) > 1:
        local_path = expanduser(local_path)
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        for blob in blobs:
            filename = blob.name[len(gcs_path) :]
            local_f_path = os.path.join(local_path, filename)
            dir_path = os.path.dirname(local_f_path)

            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                except Exception:
                    pass
            blob.download_to_filename(os.path.join(local_path, filename))
    # Only download single file - e.g. zip compressed experiment
    else:
        for blob in blobs:
            filename = blob.name.split("/")[1]
            blob.download_to_filename(filename)


def zipdir(path: str, zip_fname: str):
    """Zip a directory to upload afterwards to GCloud Storage."""
    # ziph is zipfile handle
    ziph = zipfile.ZipFile(zip_fname, "w", zipfile.ZIP_DEFLATED)
    # Get rid of redundant part of path
    prefix_len = len(path)
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(
                os.path.join(root, file), os.path.join(root[prefix_len + 1 :], file)
            )
    ziph.close()


def send_gcloud_zip(
    local_fname: str, local_zip_fname: str, delete_after_upload: bool = False
):
    """Zip & upload experiment dir to Gcloud storage."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 1. Get experiment hash from the protocol db
    gcloud_hash_fname = "experiments/" + local_zip_fname

    # 2. Zip compress the experiment
    zipdir(local_fname, local_zip_fname)

    # 3. Upload the zip file to the GCS bucket
    upload_local_dir_to_gcs(local_path=local_zip_fname, gcs_path=gcloud_hash_fname)
    logger.info(f"UPLOAD GCS - {gcloud_hash_fname}")

    # 4. Delete the .zip file & the folder if desired
    if delete_after_upload:
        os.remove(local_zip_fname)
        shutil.rmtree(local_fname, ignore_errors=True)
        logger.info(f"DELETED - experiment dir + .zip file")


def get_gcloud_zip(
    protocol_db: MLEProtocol,
    experiment_id: str,
    local_dir_name: Union[None, str] = None,
):
    """Download zipped experiment from GCS. Unpack & clean up."""
    # Ensure the right prefix
    while True:
        if experiment_id[:5] != "e-id-":
            experiment_id = "e-id-" + experiment_id

        if experiment_id not in protocol_db.experiment_ids:
            time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
            print(time_t, "The experiment you try to retrieve does not exist")
            experiment_id = input(time_t + " Which experiment do you want to retrieve?")
        else:
            break

    # Get unique hash id & download the experiment results folder
    hash_to_store = protocol_db.get(experiment_id, "e-hash")
    local_hash_fname = hash_to_store + ".zip"
    gcloud_hash_fname = "experiments/" + local_hash_fname
    download_gcs_dir(gcloud_hash_fname)

    # Unzip the retrieved file
    if local_dir_name is None:
        with zipfile.ZipFile(local_hash_fname, "r") as zip_ref:
            zip_ref.extractall(experiment_id)
    else:
        with zipfile.ZipFile(local_hash_fname, "r") as zip_ref:
            zip_ref.extractall(local_dir_name)

    # Delete the zip file
    os.remove(local_hash_fname)

    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    # Goodbye message if successful
    print(
        time_t,
        f"Successfully retrieved {experiment_id}" f" - from GCS",
    )
    print(time_t, f"Remote Path: {gcloud_hash_fname}")

    # Update protocol retrieval status of the experiment
    protocol_db.update(experiment_id, "retrieved_results", True)
    return gcloud_hash_fname
