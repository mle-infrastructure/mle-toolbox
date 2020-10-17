import os
import paramiko
from scp import SCPClient
from sshtunnel import SSHTunnelForwarder
from google.cloud import storage
from os.path import expanduser
import logging
import zipfile
import shutil
from datetime import datetime

from .general import determine_resource, load_mle_toolbox_config
from .protocol_experiment import load_experiment_db


def get_file_scp(local_dir_name: str, file_path: str, server: str, user: str,
                 password: str, port: int=22):
    """ Simple SSH connection & SCP retrieval. """
    # Generate dir to save received files in
    path_to_store = os.path.join(os.getcwd(), local_dir_name)
    if not os.path.exists(path_to_store):
        os.makedirs(path_to_store)
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    scp = SCPClient(client.get_transport())
    # Copy over the file
    scp.get(file_path, local_path=path_to_store, recursive=True)


def get_file_jump_scp(local_dir_name: str, file_path: str,
                      jump_host_server: str, main_host_server: str,
                      user: str, password: str, port: int=22):
    """ SSH connection via jumphost & SCP retrieval. """
    # Generate dir to save received files in
    path_to_store = os.path.join(os.getcwd(), local_dir_name)
    if not os.path.exists(path_to_store):
        os.makedirs(path_to_store)
    # Copy over the file
    with SSHTunnelForwarder(
        (jump_host_server, port),
        ssh_username=user,
        ssh_password=password,
        remote_bind_address=(main_host_server, port)
    ) as tunnel:
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=tunnel.local_bind_host,
                       port=tunnel.local_bind_port,
                       username=user, password=password)
        scp = SCPClient(client.get_transport())
        scp.get(file_path, local_path=path_to_store, recursive=True)


def setup_proxy_server():
    """ Set the port to tunnel for internet connection. """
    cc = load_mle_toolbox_config()
    if determine_resource() == "slurm-cluster":
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = expanduser(cc.gcp.slurm_credentials_path)
        if cc.slurm.info.http_proxy is not None:
            os.environ["HTTP_PROXY"] = cc.slurm.http_proxy
            os.environ["HTTPS_PROXY"] = cc.slurm.https_proxy
    elif determine_resource() == "sge-cluster":
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = expanduser(cc.gcp.sge_credentials_path)
        if cc.sge.info.http_proxy is not None:
            os.environ["HTTP_PROXY"] = cc.sge.http_proxy
            os.environ["HTTPS_PROXY"] = cc.sge.https_proxy


def get_gcloud_db(number_of_connect_tries: int=5):
    """ Pull latest experiment database from gcloud storage. """
    # Load in cluster configuration
    cc = load_mle_toolbox_config()
    # Set environment variable for gcloud credentials & proxy remote
    setup_proxy_server()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            # Connect to project and bucket
            client = storage.Client(cc.gcp.project_name)
            bucket = client.get_bucket(cc.gcp.bucket_name,
                                       timeout=20)
            # Download blob to db file
            blob = bucket.blob(cc.gcp.protocol_fname)
            with open(expanduser(cc.general.local_protocol_fname), 'wb') as file_obj:
                blob.download_to_file(file_obj)
            logger.info("Pulled from GCloud Storage - {}".format(cc.gcp.protocol_fname))
            return 1
        except Exception as ex:
            if type(ex).__name__ == "NotFound":
                logger.info("No DB found in GCloud Storage - {}".format(cc.gcp.protocol_fname))
                logger.info("New DB will be created - {}/{}".format(cc.gcp.project_name,
                                                                    cc.gcp.bucket_name))
                return 1
            else:
                logger.info("Attempt {}/{} - Failed pulling from GCloud Storage - {}".format(i+1,
                                                                                             number_of_connect_tries,
                                                                                             type(ex).__name__))
    # If after 5 pulls no successful connection established - return failure
    return 0


def send_gcloud_db(number_of_connect_tries: int=5):
    """ Send updated database back to gcloud storage. """
    # Load in cluster configuration
    cc = load_mle_toolbox_config()
    # Set environment variable for gcloud credentials & proxy remote
    setup_proxy_server()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            # Connect to project and bucket
            client = storage.Client(cc.gcp.project_name)
            bucket = client.get_bucket(cc.gcp.bucket_name, timeout=20)
            blob = bucket.blob(cc.gcp.protocol_fname)
            blob.upload_from_filename(filename=expanduser(cc.general.local_protocol_fname))
            logger.info("Send to GCloud Storage - {}".format(cc.gcp.protocol_fname))
            return 1
        except:
            logger.info("Attempt {}/{} - Failed sending to GCloud Storage".format(i+1,
                                                                                  number_of_connect_tries))
    # If after 5 pulls no successful connection established - return failure
    return 0


def upload_local_directory_to_gcs(local_path: str, gcs_path: str,
                                  number_of_connect_tries: int=5):
    """ Send entire dir (recursively) to Google Cloud Storage Bucket. """
    # Load in cluster configuration
    cc = load_mle_toolbox_config()
    # Set environment variable for gcloud credentials & proxy remote
    setup_proxy_server()

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(cc.gcp.project_name)
            bucket = client.get_bucket(cc.gcp.bucket_name, timeout=20)
        except:
            logger.info(f"Attempt {i+1}/{number_of_connect_tries} - Failed sending to GCloud Storage")

    def upload_single_file(local_path, gcs_path, bucket):
        # Recursively upload the folder structure
        if os.path.isdir(local_path):
            for local_file in glob.glob(os.path.join(local_path, '**')):
                if not os.path.isfile(local_file):
                   upload_single_file(local_file, os.path.join(gcs_path, os.path.basename(local_file)), bucket)
                else:
                   remote_path = os.path.join(gcs_path, local_file[1 + len(local_path):])
                   blob = bucket.blob(remote_path)
                   blob.upload_from_filename(local_file)
        # Only upload single file - e.g. zip compressed experiment
        else:
            remote_path = gcs_path
            blob = bucket.blob(remote_path)
            blob.upload_from_filename(local_path)
    upload_single_file(local_path, gcs_path, bucket)


def download_gcs_directory_to_local(gcs_path: str, local_path: str="",
                                    number_of_connect_tries: int=5):
    """ Download entire dir (recursively) from Google Cloud Storage Bucket. """
    # Load in cluster configuration
    cc = load_mle_toolbox_config()
    # Set environment variable for gcloud credentials & proxy remote
    setup_proxy_server()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    for i in range(number_of_connect_tries):
        try:
            client = storage.Client(cc.gcp.project_name)
            bucket = client.get_bucket(cc.gcp.bucket_name, timeout=20)
        except:
            logger.info(f"Attempt {i+1}/{number_of_connect_tries} - Failed sending to GCloud Storage")

    blobs = bucket.list_blobs(prefix=gcs_path)  # Get list of files

    blobs = list(blobs)
    # Recursively download the folder structure
    if len(blobs) > 1:
        local_path = expanduser(local_path)
        if not os.path.exists(local_path):
            os.makedirs(local_path)
        for blob in blobs:
            filename = blob.name[len(gcs_path):]
            local_f_path = os.path.join(local_path, filename)
            dir_path = os.path.dirname(local_f_path)

            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            blob.download_to_filename(os.path.join(local_path, filename))
    # Only download single file - e.g. zip compressed experiment
    else:
        for blob in blobs:
            filename = blob.name.split('/')[1]
            blob.download_to_filename(filename)


def zipdir(path: str, zip_fname: str):
    """ Zip a directory to upload afterwards to GCloud Storage. """
    # ziph is zipfile handle
    ziph = zipfile.ZipFile(zip_fname, 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))
    ziph.close()


def send_gcloud_zip_experiment(experiment_dir: str, experiment_id: str,
                               delete_after_upload: bool=False):
    """ Zip & upload experiment dir to Gcloud storage. """
    # 0. Set environment variable for gcloud credentials & proxy remote
    setup_proxy_server()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 1. Get experiment hash from the protocol db
    db, all_experiment_ids, last_experiment_id = load_experiment_db()
    hash_to_store = db.dget(experiment_id, "e-hash")
    local_hash_fname = hash_to_store + ".zip"
    gcloud_hash_fname = "experiments/" + local_hash_fname

    # 2. Zip the experiment
    zipdir(experiment_dir, local_hash_fname)

    # 3. Upload the zip file to the GCS bucket
    upload_local_directory_to_gcs(local_path=local_hash_fname,
                                  gcs_path=gcloud_hash_fname)
    logger.info(f"UPLOAD - {experiment_id}: {gcloud_hash_fname}")

    # 4. Update protocol with info
    db.dadd(experiment_id, ("stored_in_gcloud", True))
    db.dump()

    # 5. Delete the .zip file & the folder if desired
    if delete_after_upload:
        os.remove(local_hash_fname)
        shutil.rmtree(experiment_dir, ignore_errors=True)
        logger.info(f"DELETED - {experiment_id}: experiment dir + .zip file")


def get_gcloud_zip_experiment(db, experiment_id: str,
                              all_experiment_ids: list):
    """ Download zipped experiment from GCS. Unpack & clean up. """
    # Ensure the right prefix
    while True:
        if experiment_id[:5] != "e-id-":
            experiment_id = "e-id-" + experiment_id

        if experiment_id not in all_experiment_ids:
            print(time_t, "The experiment you try to retrieve does not exist")
            experiment_id = input(time_t + " Which experiment do you want to retrieve?")
        else:
            break

    # Get unique hash id & download the experiment results folder
    hash_to_store = db.dget(experiment_id, "e-hash")
    local_hash_fname = hash_to_store + ".zip"
    gcloud_hash_fname = "experiments/" + local_hash_fname
    download_gcs_directory_to_local(gcloud_hash_fname)

    # Unzip the retrieved file
    with zipfile.ZipFile(local_hash_fname, 'r') as zip_ref:
        zip_ref.extractall(experiment_id)

    # Delete the zip file
    os.remove(local_hash_fname)

    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    # Goodbye message if successful
    print(time_t, f"Successfully retrieved {experiment_id} - from GCS {gcloud_hash_fname}")

    # Update protocol retrieval status of the experiment
    db.dadd(experiment_id, ("retrieved_results", True))
    db.dump()
