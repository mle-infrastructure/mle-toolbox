import pdfkit
import markdown2
from dotmap import DotMap
from .markdown_generator import MarkdownGenerator
from .figure_generator import FigureGenerator


def generate_reports(db, e_id):
    """ Generate md/html/pdf report of experiment from db/results dir.
        Outputs: <e_id>.md, <e_id>.html, <e_id>.pdf
    """
    # TODO: Make report generation depend on the type of experiment
    # 1. Get the experiment data from the protocol db
    report_data = DotMap(db.get(e_id))

    # 2. Write the relevant data to the markdown report file
    md_report_fname = generate_markdown(e_id, report_data)

    # 3. Add these figures to the html report file used to generate PDF
    fig_generator = FigureGenerator(report_data.exp_retrieval_path)
    figure_fnames = fig_generator.generate_all_1D_figures()

    # 4. Generate all figures to show in report
    html_report_fname = generate_html(md_report_fname, figure_fnames)

    # 5. Generate the PDF file.
    generate_pdf()
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
