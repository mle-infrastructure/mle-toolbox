import time
from rich.live import Live

from mle_toolbox.utils import (load_mle_toolbox_config,
                               determine_resource)
from mle_toolbox.monitor import (layout_mle_dashboard,
                                 update_mle_dashboard)


def monitor():
    """ Initialize & live update rich dashboard with cluster data. """
    # Load toolbox configuration
    cc = load_mle_toolbox_config()

    # Get host resource [local, sge-cluster, slurm-cluster]
    resource = determine_resource()
    util_hist = {"rel_mem_util": [], "rel_cpu_util": [],
                 "timestamps": []}

    if cc.general.use_gcloud_protocol_sync:
        try:
            # Import of helpers for GCloud storage of results/protocol
            from mle_toolbox.remote.gcloud_transfer import get_gcloud_db
            accessed_remote_db = get_gcloud_db()
        except ImportError as err:
            raise ImportError("You need to install `google-cloud-storage` to "
                              "synchronize protocols with GCloud. Or set "
                              "`use_glcoud_protocol_sync = False` in your "
                              "config file.")

    layout = layout_mle_dashboard()
    layout, util_hist = update_mle_dashboard(layout, resource, util_hist)

    # Start timer for GCS pulling of protocol db
    start_t = time.time()
    # Run the live updating of the dashboard
    with Live(layout, refresh_per_second=10, screen=True):
        while True:
            layout, util_hist = update_mle_dashboard(layout, resource, util_hist)
            # Every 10 minutes pull the newest DB from GCS
            if time.time() - start_t > 600:
                if cc.general.use_gcloud_protocol_sync:
                    accessed_remote_db = get_gcloud_db()
                start_t = time.time()
            time.sleep(1)
