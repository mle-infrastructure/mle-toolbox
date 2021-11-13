from mle_monitor import MLEProtocol
from mle_toolbox import mle_config


def protocol():
    protocol_db = MLEProtocol(
        mle_config.general.local_protocol_fname,
        mle_config.general.use_gcloud_protocol_sync,
        mle_config.gcp.project_name,
        mle_config.gcp.bucket_name,
        mle_config.gcp.protocol_fname,
        mle_config.gcp.credentials_path,
    )
    protocol_db.summary(tail=30, verbose=True, full=True)
