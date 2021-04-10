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


from .generate_markdown import MarkdownGenerator
from .generate_figures import FigureGenerator
from .generate_reports import ReportGenerator


__all__ = [
           "MarkdownGenerator",
           "FigureGenerator",
           "ReportGenerator",
          ]
