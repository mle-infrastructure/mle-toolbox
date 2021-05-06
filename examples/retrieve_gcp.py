from mle_toolbox import mle_config
from mle_toolbox.remote.gcloud_transfer import download_gcs_dir
import os

download_gcs_dir(gcs_path=os.path.join(mle_config.gcp.results_dir,
                                       "experiments/ode/"),
                 local_path="./experiments/ode/")
