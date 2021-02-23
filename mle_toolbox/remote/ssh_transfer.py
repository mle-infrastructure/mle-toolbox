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
            os.environ["HTTP_PROXY"] = cc.slurm.info.http_proxy
            os.environ["HTTPS_PROXY"] = cc.slurm.info.https_proxy
    elif determine_resource() == "sge-cluster":
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = expanduser(cc.gcp.sge_credentials_path)
        if cc.sge.info.http_proxy is not "":
            os.environ["HTTP_PROXY"] = cc.sge.info.http_proxy
            os.environ["HTTPS_PROXY"] = cc.sge.info.https_proxy


class SSH_Manager(object):
    """ SSH client for file transfer & local 2 remote experiment exec. """
    def __init__(self, remote_resource: str):
        """ Set the credentials & resource details. """
        setup_proxy_server()
        self.cc = load_mle_toolbox_config()
        self.remote_resource = remote_resource

        # Set credentials depending on remote resource
        if self.remote_resource == "sge-cluster":
            self.main_server = self.cc.sge.info.main_server_name
            self.jump_server = self.cc.sge.info.jump_server_name
            self.port = self.cc.sge.info.ssh_port
            self.user = self.cc.sge.credentials.user_name
            self.password = self.cc.sge.credentials.password
        elif self.remote_resource == "slurm-cluster":
            self.main_server = self.cc.slurm.info.main_server_name
            self.jump_server = self.cc.slurm.info.jump_server_name
            self.port = self.cc.slurm.info.ssh_port
            self.user = self.cc.slurm.credentials.user_name
            self.password = self.cc.slurm.credentials.password

        # We are always using tunnel even if not necessary!
        if self.jump_server == '':
            self.jump_server = self.main_server

    def generate_tunnel(self):
        """ Generate a tunnel through the jump host. """
        return SSHTunnelForwarder((self.jump_server, self.port),
                                  ssh_username=self.user,
                                  ssh_password=self.password,
                                  remote_bind_address=(self.main_server,
                                                       self.port))

    def connect(self, tunnel):
        """ Connect to the ssh client. """
        while True:
            try:
                client = paramiko.SSHClient()
                client.load_system_host_keys()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(hostname=tunnel.local_bind_host,
                               port=tunnel.local_bind_port,
                               username=self.user, password=self.password,
                               timeout=100)
                break
            except:
                continue
        return client

    def sync_dir(self, local_dir_name, remote_dir_name):
        """ Clone/sync over a local directory to remote server. """
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            scp = SCPClient(client.get_transport())
            scp.put(local_dir_name, remote_dir_name, recursive=True)
            client.close()
        return

    def execute_command(self, cmd_to_exec: str):
        """ Execute a shell command on the remote server. """
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            stdin, stdout, stderr = client.exec_command(cmd_to_exec, get_pty=True)
            for l in stderr:
                print(l)
            client.close()
        return

    def read_file(self, file_name: str):
        """ Read a file from remote server and return it. """
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            ftp = client.open_sftp()
            # Something doesnt work here
            remote_file = ftp.open(file_name)
            all_lines = []
            try:
                for line in list(remote_file):
                    all_lines.append(line)
            except Exception as e:
                print(e)
            ftp.close()
            client.close()
        return all_lines

    def write_to_file(self, str_to_write: str, file_name: str):
        """ Write a string to a text file on remote server. """
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            ftp = client.open_sftp()
            file = ftp.file(file_name, "w", -1)
            file.write(str_to_write)
            file.flush()
            ftp.close()
            client.close()
        return

    def get_file(self, remote_dir_name: str, local_dir_name: str):
        """ scp clone a remote directory to the local machine. """
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            scp = SCPClient(client.get_transport())
            scp.get(remote_dir_name, local_path=local_dir_name, recursive=True)
            client.close()
        return

    def delete_file(self, file_name: str):
        """ Delete a file on the remote server. """
        with self.generate_tunnel() as tunnel:
            client = self.connect(tunnel)
            ftp = client.open_sftp()
            ftp.remove(file_name)
            ftp.close()
            client.close()
        return
