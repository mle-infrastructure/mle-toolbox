""" TEMPLATE FOR POST-PROCESSING JOB FOR MLE-TOOLBOX SEARCH RESULTS
    WE PARALLELIZE DATA-GENERATION OVER NETWORKS IN EXP DIR. """
from mle_toolbox.utils import load_hyper_log
import torch.multiprocessing as mp
import argparse


def multi_proc_inner(config_fname, chkpt_fname, add_args):
    """ Core function that is parallelized for all net ckpth. """
    # In here you should write code that loads in the agent,
    # and does some form of computation. Finally, return results
    # Make sure that processes don't overlap/are self-contained
    torch.set_num_threads(1)
    return None


def main(hyper_df_fname, num_procs, figures_dir):
    """ Parallelize data-generation over network ckpth. """
    # Load in the hyperlog with all necessary info
    hyper_df = load_hyper_log(hyper_df_fname)

    # Get all results folder
    all_runs = os.listdir(grid_dir)
    all_exp_dirs = [grid_dir + name for name in all_runs
                    if os.path.isdir(grid_dir + name)]
    all_exp_dirs.sort(key=tokenize)

    # Construct input tuples - Here you specify detailed inputs
    input_tuples = []
    for i in range(len(hyper_df["network_ckpt"].index)):
        chkpt_fname = str(hyper_df["network_ckpt"].iloc[i])
        config_fname = str(hyper_df["config_fname"].iloc[i])
        add_args = 0
        input_tuples.append((config_fname, chkpt_fname, add_args))

    # Create multiprocessing pool and COMPUTE!!!
    with mp.Pool(processes=num_procs) as pool:
        results = pool.starmap(multi_proc_inner, input_tuples)

    # Reorganize and store generated data
    for i in range(len(results)):
        out1 = results[i]

    # .... Do additional post-processing of the data generated
    # E.g. create figures, store dataframes, etc.


def get_post_proc_args():
    """ Specify additional command line input to post-proc job. """
    parser = argparse.ArgumentParser()
    #========================== BASE INPUTS ========================#
    parser.add_argument('-num_procs', '--number_processes',
                        action="store", default=20,
                        help='Example input 1.')
    parser.add_argument('-figures_dir', '--figures_directory',
                        action="store", default="figures",
                        help='File path to store figure.')
    parser.add_argument('-hyper_df', '--hyper_df_fname',
                        action="store", default="figures",
                        help='File path to Hyperlog.')
    #==================== ADDITIONAL INPUTS ========================#
    parser.add_argument('-in_1', '--input_1',
                        action="store", default=100,
                        help='Example input 1.')
    parser.add_argument('-in_2', '--input_2',
                        action="store", default=100,
                        help='Example input 2.')
    return parser.parse_args()


if __name__ == "__main__":
    cmd_args = get_post_proc_args()
    main(cmd_args.hyper_df_fname,
         cmd_args.number_processes,
         cmd_args.figures_directory)

# # Parameters for the post processing job
# post_processing_args:
#     processing_fname: "template_post_proc.py"
#     processing_job_args:
#         num_logical_cores: 15
#         time_per_job: "00:05:00"
#     extra_cmd_line_input:
#         in_1: 25
#         in_2: 100
#         figures_dir: "figures_25"
