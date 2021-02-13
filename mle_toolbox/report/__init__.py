try:
    import pdfkit
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(f"{err}. You need to install `pdfkit` "
                              "to use the `mle_toolbox.report` module.")

try:
    import markdown2
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(f"{err}. You need to install `markdown2` "
                              "to use the `mle_toolbox.report` module.")


from .markdown_generator import MarkdownGenerator
from .report_experiment import generate_report


__all__ = [
           "MarkdownGenerator",
           "generate_report"
          ]
