import argparse


def main():
    """ Handle argparse/entry point script for all subcommands.
        Add one of the subcommands to `mle-toolbox <subcmd> --option <opt>`:
    - `run`: Run a new experiment on a resource available to you.
    - `retrieve`: Retrieve a completed experiment from a cluster/GCS bucket.
    - `report`: Generate set of reports (.html/.md) from experiment results.
    - `monitor`: Monitor a compute resource and view experiment protocol.
    - `sync-gcs`: Sync all new results from Google Cloud Storage.
    - `init`: Setup the toolbox .toml config with credentials/defaults.
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")

    # Build subparsers for individual subcommands
    parser_run = run_build_subparser(subparsers)
    parser_retrieve = retrieve_build_subparser(subparsers)
    parser_report = report_build_subparser(subparsers)

    # Following subcommands don't have any options - but are 'helpful' :)
    parser_monitor = monitor_build_subparser(subparsers)
    parser_sync_gcs = sync_gcs_build_subparser(subparsers)
    parser_init = init_build_subparser(subparsers)

    # Parse arguments and executed provided subcommand
    args = parser.parse_args()
    if args.command == "run":
        from .src.run import run
        run(args)
    elif args.command == "retrieve":
        from .src.retrieve import retrieve
        retrieve(args)
    elif args.command == "report":
        from .src.report import report
        report(args)
    elif args.command == "monitor":
        from .src.monitor import monitor
        monitor()
    elif args.command == "sync-gcs":
        from .src.sync_gcs import sync_gcs
        sync_gcs()
    elif args.command == "init":
        from .src.initialize import initialize
        initialize(args)
    else:
        parser.parse_args(["--help"])
    return


def run_build_subparser(subparsers):
    """ Build subparser arguments for `run` subcommand. """
    parser_run = subparsers.add_parser("run",
        help="Run a new experiment on a resource available to you.",)
    # Basic run-experiment options
    parser_run.add_argument('config_fname', metavar='C', type=str,
                            default="experiment_config.yaml",
                            help ='Filename to load config yaml from')
    parser_run.add_argument('-d', '--debug', default=False,
                            action='store_true',
                            help ='Run simulation in debug mode')
    parser_run.add_argument('-p', '--purpose', default=None, nargs='+',
                            help ='Purpose of the experiment to run')
    parser_run.add_argument('-np', '--no_protocol', default=False,
                            action='store_true',
                            help ='Run simulation in w/o protocol recording')
    parser_run.add_argument('-del', '--delete_after_upload', default=False,
                            action='store_true',
                            help ='Delete results after upload to GCloud.')
    parser_run.add_argument('-nw', '--no_welcome', default=False,
                            action='store_true',
                            help ='Do not print welcome message.')

    # Which resource to run on and whether to reconnect to running remote job
    parser_run.add_argument('-resource', '--resource_to_run', default=None,
                            help ='Resource to run experiment on '
                            '{local, sge-cluster, slurm-cluster, gcp-cloud}.')
    parser_run.add_argument('-reconnect', '--remote_reconnect',
                            default=False, action='store_true',
                            help ='Reconnects to experiment via .yaml str.')

    # Allow CLI to change base train fname/config .json/experiment dir
    parser_run.add_argument('-train_fname', '--base_train_fname', default=None,
                            help ='Python script to run exp on.')
    parser_run.add_argument('-train_config', '--base_train_config',
                            default=None,
                            help ='Base config file to load and modify.')
    parser_run.add_argument('-exp_dir', '--experiment_dir', default=None,
                            help ='Experiment directory.')
    return parser_run


def retrieve_build_subparser(subparsers):
    """ Build subparser arguments for `retrieve` subcommand. """
    parser_retrieve = subparsers.add_parser("retrieve",
        help="Retrieve a completed experiment from a cluster/GCS bucket.",)
    parser_retrieve.add_argument('-e_id', '--experiment_id', type=str,
                                 default="no-id-given",
                                 help ='Experiment ID')
    parser_retrieve.add_argument('-all_new', '--retrieve_all_new',
                                 default=False, action='store_true',
                                 help ='Retrieve all new results.')
    parser_retrieve.add_argument('-fig_dir', '--figures_dir',
                                 default=False, action='store_true',
                                 help ='Retrieve only subdir with figures.')
    parser_retrieve.add_argument('-exp_dir', '--experiment_dir',
                                 default=False, action='store_true',
                                 help ='Retrieve entire experiment dir.')
    parser_retrieve.add_argument('-local', '--retrieve_local',
                                 default=False, action='store_true',
                                 help ='Retrieve experiment dir from remote.')
    parser_retrieve.add_argument('-dir_name', '--local_dir_name',
                                 default=None, action='store_true',
                                 help ='Name of new local results directory.')
    return parser_retrieve


def report_build_subparser(subparsers):
    """ Build subparser arguments for `report` subcommand. """
    parser_report = subparsers.add_parser("report",
        help="Generate set of reports (.html/.md) from experiment results.",)
    parser_report.add_argument('-e_id', '--experiment_id', type=str,
                               default="no-id-given",
                               help ='Experiment ID')
    return parser_report


def monitor_build_subparser(subparsers):
    """ Build subparser arguments for `init` subcommand. """
    parser_monitor = subparsers.add_parser("monitor",
        help="Monitor a compute resource and view experiment protocol.",)
    return parser_monitor


def sync_gcs_build_subparser(subparsers):
    """ Build subparser arguments for `init` subcommand. """
    parser_sync = subparsers.add_parser("sync-gcs",
        help="Sync all new results from Google Cloud Storage.",)
    return parser_sync


def init_build_subparser(subparsers):
    """ Build subparser arguments for `init` subcommand. """
    parser_init = subparsers.add_parser("init",
        help="Setup the toolbox .toml config with credentials/defaults.",)
    parser_init.add_argument('-no_cli', '--no_command_line',
                             default=False, action='store_true',
                             help ='Whether to go through settings in CLI.')
    return parser_init
