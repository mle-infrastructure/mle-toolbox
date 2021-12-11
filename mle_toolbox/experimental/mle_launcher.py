from mle_toolbox import mle_config
from mle_monitor import MLEProtocol
from mle_toolbox.launch import launch_experiment


class MLELaucnher(object):
    def __init__(self, resource_name: str, job_config: dict):
        """Helper for launching experiments from a notebook."""
        self.resource_name = resource_name
        self.job_config = job_config
        self.protocol_db = MLEProtocol(
            mle_config.general.local_protocol_fname, mle_config.gcp
        )

    def launch(self):
        launch_experiment(
            self.resource_name,
            self.job_config,
            no_protocol=True,
            message_id=True,
            protocol_db=self.protocol_db,
        )
