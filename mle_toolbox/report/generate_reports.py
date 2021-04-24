import os
import logging
import pdfkit
import markdown2
from dotmap import DotMap
from .generate_markdown import MarkdownGenerator
from .generate_figures import FigureGenerator
from ..launch.prepare_experiment import prepare_logger


class ReportGenerator():
    """
    Generate md/html/pdf report of experiment from db/results dir.
    Outputs: <e_id>.md, <e_id>.html, <e_id>.pdf
    """
    def __init__(self, e_id, db, logger=None, pdf_gen=False):
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

        # Setup logger for report generation
        if logger is None:
            self.logger = prepare_logger(None, False)
        else:
            self.logger = logger

        # Whether to also generate pdf report
        self.pdf_gen = pdf_gen

    def generate_reports(self):
        """ Generate reports + generate included figures: .md, .html, .pdf. """
        self.logger.info(f'Report - BASE REPORT DIRECTORY:')
        self.logger.info(f'{self.experiment_dir}')
        # 1. Write the relevant data to the markdown report file
        self.md_report_fname = os.path.join(self.reports_dir,
                                            self.e_id + ".md")
        self.markdown_text = generate_markdown(self.e_id,
                                               self.md_report_fname,
                                               self.report_data)
        self.logger.info(f'Report - GENERATED - .md: {self.e_id + ".md"}')

        # 2a. Generate all 1D figures to show in report
        self.fig_generator = FigureGenerator(self.experiment_dir)
        figure_fnames_1D = self.fig_generator.generate_all_1D_figures()

        # 2b. If search experiment generate all 2D figures to show in report
        search_vars, search_targets = self.get_hypersearch_data()
        if len(search_vars) > 1:
            figure_fnames_2D = self.fig_generator.generate_all_2D_figures(
                                        search_vars, search_targets)

        self.figure_fnames = abs_figure_paths(self.fig_generator.figures_dir)
        self.logger.info(f'Report - GENERATED - figures - total:'
                         f' {len(self.figure_fnames)}')

        # 3. Add these figures to the html report file used to generate PDF
        self.html_report_fname = os.path.join(self.reports_dir,
                                              self.e_id + ".html")
        self.html_text = generate_html(self.html_report_fname,
                                       self.markdown_text,
                                       self.figure_fnames)
        self.logger.info(f'Report - GENERATED - .html: {self.e_id + ".html"}')

        # 4. Also add figures to the markdown text to render
        add_figures_to_markdown(self.md_report_fname, self.figure_fnames)
        self.logger.info(f'Report - UPDATED - .md with figures.')

        # 5. Generate the PDF file.
        if self.pdf_gen:
            self.pdf_report_fname = os.path.join(self.reports_dir,
                                                 self.e_id + ".pdf")
            generate_pdf(self.pdf_report_fname, self.html_text)
            self.logger.info(f'Report - GENERATED - .pdf: {self.e_id + ".pdf"}')

    def get_hypersearch_data(self):
        """ Get hypersearch variables + targets for 2D visualization loop. """
        search_vars, search_targets = [], []
        if "params_to_search" in self.report_data["job_spec_args"]:
            params = self.report_data["job_spec_args"]["params_to_search"]
            for type, var_dict in params.items():
                for var_name in var_dict.keys():
                    search_vars.append(var_name)
            search_targets = self.report_data["job_spec_args"]["eval_metrics"]
        return search_vars, search_targets


def construct_markdown_table(data_dict, exclude_keys=[],
                             table_entries_per_row=2):
    """ Construct a markdown table from a dictionary with data. """
    table, current_row, entry_counter = [], {}, 0
    for k, value in data_dict.items():
        # Only add to table row if not excluded in given list
        if k not in exclude_keys:
            current_row["Param C" + str(entry_counter+1)] = "`" + str(k) + "`"
            if type(value) == list:
                v_temp = [str(x) for x in value]
                v = ', '.join(v_temp)
            else:
                v = str(value)
            current_row["Value C" + str(entry_counter+1)] = "`" + str(v) + "`"
            entry_counter += 1

            # reset the row dictionary and append to table list
            if (entry_counter % table_entries_per_row) == 0:
                table.append(current_row)
                current_row = {}
                entry_counter = 0

    # Add final residual of row - if not already done at end of loop
    if (entry_counter % table_entries_per_row) != 0:
        table.append(current_row)
    return table


def construct_hypersearch_table(params_to_search):
    """ Construct a markdown table for the hyperparameter search ranges. """
    table, current_row, entry_counter = [], {}, 0
    for type, var_dict in params_to_search.items():
        for var_name, var_range in var_dict.items():
            current_row["Var. Type"] = "`" + str(type) + "`"
            current_row["Var. Name"] = "`" + str(var_name) + "`"
            # Combine range into single string
            try:
                v_temp = []
                for k_r, v_r in var_range.items():
                    v_temp.append(str(k_r) + ": " + str(v_r))
            except:
                v_temp = [str(x) for x in var_range]
            v = ', '.join(v_temp)
            current_row["Var. Range"] = "`" + str(v) + "`"
            # Append new row of data (variable with range data)
            table.append(current_row)
            current_row = {}
    return table


def generate_markdown(e_id, md_report_fname, report_data):
    """ Generate MD report from experiment meta data. """
    # Special treatment of dict keys/individual vars in report_data
    job_keys = ["meta_job_args", "single_job_args", "job_spec_args"]
    config_keys = ["train_config", "log_config", "net_config"]
    single_keys = ["purpose", "project_name"]

    md_generator = MarkdownGenerator(filename=md_report_fname,
                                     enable_write=False)
    with md_generator as doc:
        doc.addHeader(1, "Report: "
                      + report_data["project_name"] + " - " + e_id)

        # Meta-Data of the Experiment
        doc.addHeader(2, "Experiment Meta-Data.")
        doc.writeTextLine(f'{doc.addBoldedText("Purpose:")} ' + report_data["purpose"])

        doc.addHeader(3, "General Job Settings.")
        hyper_table = construct_markdown_table(report_data,
                                               (job_keys + config_keys +
                                                single_keys))
        doc.addTable(dictionary_list=hyper_table)

        # Experiment Configs - Meta-Job, Single-Job, Job-Spec-Args
        doc.addHeader(3, "Meta-Job-Arguments.")
        meta_table = construct_markdown_table(report_data["meta_job_args"])
        doc.addTable(dictionary_list=meta_table)

        doc.addHeader(3, "Single-Job-Arguments.")
        job_table = construct_markdown_table(report_data["single_job_args"],
                                             table_entries_per_row=3)
        doc.addTable(dictionary_list=job_table)

        doc.addHeader(3, "Job-Specific-Arguments.")
        specific_table = construct_markdown_table(report_data["job_spec_args"],
                                                  ["params_to_search"])
        doc.addTable(dictionary_list=specific_table)
        if report_data["meta_job_args"]["job_type"] == "hyperparameter-search":
            search_table = construct_hypersearch_table(
                            report_data["job_spec_args"]["params_to_search"])
            doc.addTable(dictionary_list=search_table)

        # Base Configuration Hyperparameters used in the Experiment
        doc.addHeader(2, "Base Config Hyperparameters.")
        doc.addHeader(3, "Train Configuration.")
        train_table = construct_markdown_table(report_data["train_config"])
        doc.addTable(dictionary_list=train_table)

        doc.addHeader(3, "Network Configuration.")
        net_table = construct_markdown_table(report_data["net_config"])
        doc.addTable(dictionary_list=net_table)

        doc.addHeader(3, "Logging Configuration.")
        log_table = construct_markdown_table(report_data["log_config"])
        doc.addTable(dictionary_list=log_table)

        # Generated header for figures of the Experiment
        doc.addHeader(2, "Generated Figures.")

    markdown_text = open(md_report_fname).read()
    return markdown_text


def generate_html(html_report_fname, markdown_text, figure_fnames):
    """ Generates HTML report from markdown text + adds all figures. """
    with open(html_report_fname, 'w') as output_file:
        html_text = markdown2.markdown(markdown_text, extras=["tables"])
        # Add figure inclusion to HTML text
        # By default: 2 Figures per row - 45% width
        for fig in figure_fnames:
            html_text += (f'<img src="{fig}" width="45%"'
                            + 'style="margin-right:20px">')
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


def add_figures_to_markdown(md_report_fname, figure_fnames):
    """ Add figures to markdown after html report generation. """
    with open(md_report_fname, "a+") as file_object:
        for f_name in figure_fnames:
            path, file = os.path.split(f_name)
            file_object.write("\n")
            file_object.write(f'<img src=../figures/{file} width="45%"'
                              + ' style="margin-right:20px">')


def abs_figure_paths(directory):
    """ Return all absolute figure paths to include in report. """
    abs_paths = []
    for dirpath,_,filenames in os.walk(directory):
        for f in filenames:
            if f.endswith(".png"):
                abs_paths.append(os.path.abspath(os.path.join(dirpath, f)))
    return abs_paths
