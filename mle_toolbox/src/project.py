import git
import os
import shutil


def project(cmd_args):
    """Clone template repository and clean-up"""
    git_url = "https://github.com/mle-infrastructure/mle-project"
    git.Git(".").clone(git_url)
    os.rename("mle-project", cmd_args.project_name)
    shutil.rmtree(os.path.join(cmd_args.project_name, ".git"))
    return
