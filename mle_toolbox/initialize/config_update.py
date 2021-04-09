import os
import sys
import select
import toml
from datetime import datetime

from rich import box
from rich.console import Console
from rich.table import Table

from .config_description import description_mle_config


def whether_update_config(var_name):
    """ Ask if variable should be updated - if yes, move on to details. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print("{} Do you want to update {}: [Y/N]".format(time_t, var_name),
          end=' ')
    sys.stdout.flush()
    # Loop over experiments to delete until "N" given or timeout after 60 secs
    i, o, e = select.select([sys.stdin], [], [], 60)
    if (i):
        answer = sys.stdin.readline().strip()
    else:
        answer = "N"
    sys.stdout.flush()
    # TODO: Make more robust to input errors
    return (answer == "Y")


def how_update_config(var_name, var_type):
    """ Ask how variable should be updated - get string/int. """
    time_t = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
    print("{} How do you want to update {} - {}: ".format(time_t,
                                                     var_name,
                                                     str(var_type)),
          end=' ')
    sys.stdout.flush()
    # Loop over experiments to delete until "N" given or timeout after 60 secs
    i, o, e = select.select([sys.stdin], [], [], 60)
    if (i):
        answer = sys.stdin.readline().strip()
    else:
        answer = None
    sys.stdout.flush()
    # TODO: Make more robust to input errors
    if var_type == list:
        answer = answer.strip('[]').split(',')
    return var_type(answer)


def store_mle_config(config_dict,
                     config_fname=os.path.expanduser("~/mle_config.toml")):
    """ Write the toml dictionary to a file. """
    with open(config_fname, 'w') as f:
        new_toml_string = toml.dump(config_dict, f)


def print_mle_config(mle_config):
    """ Print pretty version as rich table at init start and end. """
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Category", style="dim", width=12)
    table.add_column("Sub-Category")
    table.add_column("Variable", justify="left")
    table.add_column("Value", justify="left")
    table.add_column("Description", justify="left")
    table.add_column("Type", justify="left")

    for k in description_mle_config.keys():
        for sk in description_mle_config[k].keys():
            if k != sk:
                for var in description_mle_config[k][sk]["variables"].keys():
                    table.add_row(
                        k, sk, var,
                        str(mle_config[k][sk][var]),
                        description_mle_config[k][sk]["variables"][var]["description"],
                        str(description_mle_config[k][sk]["variables"][var]["type"])
                    )
            else:
                for var in description_mle_config[k][sk]["variables"].keys():
                    table.add_row(
                        k, "---", var,
                        str(mle_config[k][var]),
                        description_mle_config[k][sk]["variables"][var]["description"],
                        str(description_mle_config[k][sk]["variables"][var]["type"])
                    )
    table.row_styles = ["none", "dim"]
    table.border_style = "magenta"
    table.box = box.SIMPLE
    console.print(table)
