import os
import pdfkit
import markdown2
from dotmap import DotMap
from .markdown_generator import MarkdownGenerator
from .figure_generator import FigureGenerator


class ReportGenerator():
    """
    Generate md/html/pdf report of experiment from db/results dir.
    Outputs: <e_id>.md, <e_id>.html, <e_id>.pdf
    """
    def __init__(self, e_id, db):
        # TODO: Make report generation depend on the type of experiment
        # TODO: Add logging so that user gets verbose feedback
        # Get the experiment data from the protocol db
        self.e_id = e_id
        self.db = db
        self.report_data = DotMap(self.db.get(self.e_id))
        self.experiment_dir = self.report_data.exp_retrieval_path

        # Create a directory for the reports to be stored in
        self.reports_dir = os.path.join(self.experiment_dir, "reports")
        if not os.path.exists(self.reports_dir):
            try: os.makedirs(self.reports_dir)
            except: pass

    def generate_reports(self):
        # 1. Write the relevant data to the markdown report file
        self.md_report_fname = os.path.join(self.reports_dir,
                                            self.e_id + ".md")
        self.markdown_text = generate_markdown(self.e_id,
                                               self.md_report_fname,
                                               self.report_data)

        # 2. Add these figures to the html report file used to generate PDF
        self.fig_generator = FigureGenerator(self.experiment_dir)
        self.figure_fnames = self.fig_generator.generate_all_1D_figures()

        # 3. Generate all figures to show in report
        self.html_report_fname = os.path.join(self.reports_dir,
                                              self.e_id + ".html")
        self.html_text = generate_html(self.html_report_fname,
                                       self.markdown_text,
                                       self.figure_fnames)

        # TODO: Afterwards also add figures to the markdown text
        # But in markdown syntax! HMTL addtextline seems to get scrambled

        # 4. Generate the PDF file.
        self.pdf_report_fname = os.path.join(self.reports_dir,
                                             self.e_id + ".pdf")
        generate_pdf(self.pdf_report_fname, self.html_text)


def generate_markdown(e_id, md_report_fname, report_data):
    """ Generate MD report from experiment meta data. """
    with MarkdownGenerator(filename=md_report_fname,
                           enable_write=False) as doc:
        doc.addHeader(1, "Report: "
                      + report_data["project_name"] + " - " + e_id)

        # Meta-Data of the Experiment
        doc.addHeader(2, "Experiment Meta-Data.")
        doc.writeTextLine(f'{doc.addBoldedText("Purpose:")} ' + report_data["purpose"])

        # Hyperparameters used in the Experiment
        doc.addHeader(2, "Hyperparameters.")
        table = [
            {"Parameter": "col1row1", "Value": "col2row1"},
            {"Parameter": "col1row2", "Value": "col2row2"}
        ]
        doc.addTable(dictionary_list=table)

        # Generated header for figures of the Experiment
        doc.addHeader(2, "Generated 1D Figures.")

    markdown_text = open(md_report_fname).read()
    return markdown_text


def generate_html(html_report_fname, markdown_text, figure_fnames):
    """ Generates HTML report from markdown text + adds all figures. """
    with open(html_report_fname, 'w') as output_file:
        html_text = markdown2.markdown(markdown_text, extras=["tables"])
        # Add figure inclusion to HTML text
        # By default: 2 Figures per row - 45% width
        for fig in figure_fnames:
            html_text += f'<img src="{fig}" width="45%" style="margin-right:20px">'
        output_file.write(html_text)
    return html_text


def generate_pdf(pdf_report_fname, html_text):
    """ Generates a PDF report from the transformed html text. """
    pdfkit.from_string(html_text, pdf_report_fname,
                       options={"enable-local-file-access": None,
                                'page-size': 'A4',
                                'dpi': 400,
                                'print-media-type': '',
                                'disable-smart-shrinking': '',
                                'quiet': ''})
