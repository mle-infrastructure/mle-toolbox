import time
from rich.live import Live
from mle_toolbox.utils import (load_mle_toolbox_config,
                               determine_resource)
from mle_toolbox.protocol import load_local_protocol_db
from mle_toolbox.monitor import (layout_mle_dashboard,
                                 update_mle_dashboard)


def monitor():
    """ Initialize & live update rich dashboard with cluster data. """
    # Load toolbox configuration
    cc = load_mle_toolbox_config()

    # Get host resource [local, sge-cluster, slurm-cluster]
    resource = determine_resource()

    # Start storing utilisation history
    util_hist = {"rel_mem_util": [],
                 "rel_cpu_util": [],
                 "times_date": [],
                 "times_hour": []}

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

    # Get newest data depending on resourse!
    db, all_e_ids, last_e_id = load_local_protocol_db()

    # Generate the dashboard layout and display first data
    layout = layout_mle_dashboard()
    layout, util_hist = update_mle_dashboard(layout, resource, util_hist,
                                             db, all_e_ids, last_e_id)

    # Start timers for GCS pulling and reloading of local protocol db
    timer_gcs = time.time()
    timer_db = time.time()

    # Run the live updating of the dashboard
    with Live(layout, refresh_per_second=10, screen=True):
        while True:
            layout, util_hist = update_mle_dashboard(layout, resource,
                                                     util_hist, db,
                                                     all_e_ids, last_e_id)

            # Every 10 seconds reload local database file
            if time.time() - timer_gcs > 10:
                db, all_e_ids, last_e_id = load_local_protocol_db()
                timer_db = time.time()

            # Every 10 minutes pull the newest DB from GCS
            if time.time() - timer_gcs > 600:
                if cc.general.use_gcloud_protocol_sync:
                    accessed_remote_db = get_gcloud_db()
                timer_gcs = time.time()

            # Limit memory to approx. last 27 hours
            util_hist["times_date"] = util_hist["times_date"][:100000]
            util_hist["times_hour"] = util_hist["times_hour"][:100000]
            util_hist["rel_mem_util"] = util_hist["rel_mem_util"][:100000]
            util_hist["rel_cpu_util"] = util_hist["rel_cpu_util"][:100000]

            # Wait a second
            time.sleep(1)
