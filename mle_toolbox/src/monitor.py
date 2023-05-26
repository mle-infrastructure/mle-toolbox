from mle_toolbox import mle_config
from mle_toolbox.utils import determine_resource, setup_proxy_server
from mle_monitor import MLEDashboard, MLEProtocol, MLEResource


def monitor():
    """Initialize & live update rich dashboard with cluster data."""
    # Get newest data depending on resourse!
    setup_proxy_server()
    protocol = MLEProtocol(mle_config.general.local_protocol_fname, mle_config.gcp)
    resource_name = determine_resource()
    if resource_name == "sge-cluster":
        monitor_config = {"queues": mle_config.sge.info.queues}
    elif resource_name == "slurm-cluster":
        monitor_config = {"partitions": mle_config.slurm.info.partitions}
    else:
        resource_name = "local"
        monitor_config = {}
    resource = MLEResource(resource_name, monitor_config)
    dashboard = MLEDashboard(protocol, resource)

    # Run the dashboard in a while loop
    dashboard.live()
