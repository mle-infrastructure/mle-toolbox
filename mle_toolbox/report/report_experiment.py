import pdfkit
import markdown2
from .markdown_generator import MarkdownGenerator
#from .figure_generator import FigureGenerator

def generate_reports(db, e_id):
    """ Generate md/html/pdf report of experiment from db/results dir.
        Outputs: <e_id>.md, <e_id>.html, <e_id>.pdf
    """
    # TODO: Make report generation depend on the type of experiment
    # 1. Get the experiment data from the protocol db
    report_data = db.get(e_id)

    # 2. Write the relevant data to the markdown report file
    md_report_fname =

    # 3. Generate all figures to show in report
    html_report_fname =

    # 4. Add these figures to the html report file used to generate PDF
    figure_paths =
    # 5. Generate the PDF file.
    return


def generate_markdown(e_id, report_data):
    """ Generate MD report from experiment meta data. """
    return md_report_fname


def generate_html():
    """ Generates HTML report from markdown text + adds all figures. """
    return html_report_fname


def generate_pdf():
    """ Generates a PDF report from the transformed html text. """
    return
