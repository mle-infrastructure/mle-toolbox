# Welcome to the MLE-Infrastructure

<a href="https://roberttlange.github.io/mle-toolbox/thumbnails/logo_overview.png"><img src="https://roberttlange.github.io/mle-toolbox/thumbnails/logo_overview.png" width="800" align="center" /></a>

The MLE-Infrastructure provides a reproducible workflow for distributed running Machine Learning experiments (MLE) with minimal overhead. The core consists of 5 packages:

- [`mle-logging`](https://github.com/RobertTLange/mle-logging): Experiment logging with easy multi-seed and configuration aggregation.
- [`mle-hyperopt`](https://github.com/RobertTLange/mle-hyperopt): Hyperparameter Optimization with config export, refinement & reloading.
- [`mle-monitor`](https://github.com/RobertTLange/mle-monitor): Monitor cluster/cloud VM resource utilization & protocol experiments.
- [`mle-launcher`](https://github.com/RobertTLange/mle-launcher): Schedule & monitor jobs on Slurm, GridEngine clusters & GCP VMs.
- [`mle-toolbox`](https://github.com/RobertTLange/mle-toolbox): Glue everything together to manage & post-process experiments.

A template repository structure of an infrastructure-based project can be found in the [`mle-project`](https://github.com/RobertTLange/mle-project-template).

**Note**: `mle-logging`, `mle-hyperopt`, `mle-monitor` and `mle-launcher` are standalone packages and can be used independently of the experiment scheduling utilities provided by the `mle-toolbox`.


| `mle-logging` | `mle-hyperopt` | `mle-monitor`  | `mle-launcher` |  `mle-toolbox` |
|:----:|:----: |:----: |:----:| :----:|
| [Repo](https://github.com/RobertTLange/mle-logging)/[Docs](https://roberttlange.github.io/mle-infrastructure/logging/mle_logging/) | [Repo](https://github.com/RobertTLange/mle-hyperopt)/[Docs](https://roberttlange.github.io/mle-infrastructure/hyperopt/mle_hyperopt/) | [Repo](https://github.com/RobertTLange/mle-monitor)/[Docs](https://roberttlange.github.io/mle-infrastructure/monitor/mle_monitor/)  | [Repo](https://github.com/RobertTLange/mle-launcher)/[Docs](https://roberttlange.github.io/mle-infrastructure/launcher/mle_launcher) |[Repo](https://github.com/RobertTLange/mle-toolbox)/[Docs](https://roberttlange.github.io/mle-infrastructure/toolbox/mle_toolbox) |
|<img src="https://github.com/RobertTLange/mle-logging/blob/main/docs/logo_transparent.png?raw=true" alt="drawing" width="120"/>|  <img src="https://github.com/RobertTLange/mle-hyperopt/blob/main/docs/logo_transparent.png?raw=true" alt="drawing" width="120"/> |  <img src="https://github.com/RobertTLange/mle-hyperopt/blob/main/docs/logo_transparent.png?raw=true" alt="drawing" width="120"/> | <img src="https://github.com/RobertTLange/mle-hyperopt/blob/main/docs/logo_transparent.png?raw=true" alt="drawing" width="120"/> | <img src="https://github.com/RobertTLange/mle-hyperopt/blob/main/docs/logo_transparent.png?raw=true" alt="drawing" width="120"/> |
