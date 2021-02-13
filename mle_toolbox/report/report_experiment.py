import pdfkit
import markdown2
from dotmap import DotMap
from .markdown_generator import MarkdownGenerator
from .figure_generator import FigureGenerator


def generate_reports(e_id, db):
    """ Generate md/html/pdf report of experiment from db/results dir.
        Outputs: <e_id>.md, <e_id>.html, <e_id>.pdf
    """
    # TODO: Make report generation depend on the type of experiment
    # 1. Get the experiment data from the protocol db
    report_data = DotMap(db.get(e_id))

    # 2. Write the relevant data to the markdown report file
    md_report_fname, markdown_text = generate_markdown(e_id, report_data)

    # 3. Add these figures to the html report file used to generate PDF
    fig_generator = FigureGenerator(report_data.exp_retrieval_path)
    figure_fnames = fig_generator.generate_all_1D_figures()

    # 4. Generate all figures to show in report
    html_report_fname, html_text = generate_html(e_id, markdown_text,
                                                 figure_fnames)

    # 5. Generate the PDF file.
    pdf_report_fname = generate_pdf(e_id, html_text)
    return md_report_fname, html_report_fname, pdf_report_fname


def generate_markdown(e_id, report_data):
    """ Generate MD report from experiment meta data. """
    md_report_fname = e_id + ".md"

    with MarkdownGenerator(filename=md_report_fname,
                           enable_write=False) as doc:
        doc.addHeader(1, "Experiment Protocol: "
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
        doc.addHeader(2, "Generated Figures.")

    markdown_text = open(md_report_fname).read()
    return md_report_fname, markdown_text


def generate_html(e_id, markdown_text, figure_fnames):
    """ Generates HTML report from markdown text + adds all figures. """
    html_report_fname = e_id + ".html"

    with open(html_report_fname, 'w') as output_file:
        html_text = markdown2.markdown(markdown_text, extras=["tables"])
        for fig in figure_fnames:
            html_text += f'<img src="{fig}" width="50%" style="margin-right:20px">'
        output_file.write(html_text)
    return html_report_fname, html_text


def generate_pdf(e_id, html_text):
    """ Generates a PDF report from the transformed html text. """
    pdf_report_fname = e_id + '.pdf'
    pdfkit.from_string(html_text, pdf_report_fname,
                       options={"enable-local-file-access": None,
                                'page-size': 'A4',
                                'dpi': 400,
                                'print-media-type': '',
                                'disable-smart-shrinking': ''})
    return pdf_report_fname
