import os
import paramiko
from scp import SCPClient
from sshtunnel import SSHTunnelForwarder
from os.path import expanduser

from ..utils.general import determine_resource, load_mle_toolbox_config


def setup_proxy_server():
    """ Set Gcloud creds & port to tunnel for internet connection. """
    cc = load_mle_toolbox_config()
    if determine_resource() == "slurm-cluster":
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = expanduser(cc.gcp.slurm_credentials_path)
        if cc.slurm.info.http_proxy is not "":
            os.environ["HTTP_PROXY"] = cc.slurm.http_proxy
            os.environ["HTTPS_PROXY"] = cc.slurm.https_proxy
    elif determine_resource() == "sge-cluster":
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = expanduser(cc.gcp.sge_credentials_path)
        if cc.sge.info.http_proxy is not "":
            os.environ["HTTP_PROXY"] = cc.sge.http_proxy
            os.environ["HTTPS_PROXY"] = cc.sge.https_proxy


def createSSHClient(server: str, user: str, password: str, port: int=22):
    """ Create an ssh connection. """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server, port, user, password)
    return client


def get_file_scp(local_dir_name: str, file_path: str, server: str,
                 user: str, password: str, port: int=22):
    """ Simple SSH connection & SCP retrieval. """
    # Generate dir to save received files in
    path_to_store = os.path.join(os.getcwd(), local_dir_name)
    if not os.path.exists(path_to_store):
        os.makedirs(path_to_store)
    client = createSSHClient(server, user, password, port)
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
