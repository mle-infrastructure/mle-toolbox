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


from .generate_reports import (user_generate_reports,
                               auto_generate_reports)
from .markdown_generator import MarkdownGenerator
from .figure_generator import FigureGenerator
from .report_generator import ReportGenerator


__all__ = [
           "user_generate_reports",
           "auto_generate_reports",
           "MarkdownGenerator",
           "FigureGenerator",
           "ReportGenerator",
          ]
