from mle_toolbox import mle_config
from mle_toolbox.utils import determine_resource
from mle_monitor import MLEDashboard, MLEProtocol, MLEResource


def monitor():
    """Initialize & live update rich dashboard with cluster data."""
    # Get newest data depending on resourse!
    protocol = MLEProtocol(
        mle_config.general.local_protocol_fname,
        mle_config.general.use_gcloud_protocol_sync,
        mle_config.gcp.project_name,
        mle_config.gcp.bucket_name,
        mle_config.gcp.protocol_fname,
        mle_config.gcp.credentials_path,
    )
    resource_name = determine_resource()
    resource = MLEResource(resource_name)
    dashboard = MLEDashboard(protocol, resource)

    # Run the dashboard in a while loop
    dashboard.live()
