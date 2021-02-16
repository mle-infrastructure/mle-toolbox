import tempfile
from pathlib import Path
from os import linesep
from typing import List
from html import escape
from string import punctuation


HEADER = "#"
HORIZONTAL_RULE = "---"
CODE_BLOCK = "```"
SINGLE_LINE_BLOCKQUOTE = ">"
HTML_SPACE = ""
DEFAULT_FILE_LOCATION = "default_file"
MAX_HEADER_LEVEL = 6
MIN_HEADER_LEVEL = 1
TOC_LINE_POSITION = 2

# This MarkdownGenerator class takes heavy inspiration from the package
# python-markdown-generator: github.com/Nicceboy/python-markdown-generator
# And adapts it for the purposes of the mle-toolbox - directly returns md/html

class MarkdownGenerator:
    """ Generating GitHub flavored Markdown. Init by using 'with' statement."""
    def __init__(self, document=None, filename=None,
                 syntax=None, root_object=True,
                 tmp_dir=None, header_data_array=None,
                 header_index=None, document_data_array=None,
                 enable_write=True, enable_TOC=True):
        """
        Constructor method for MarkdownGenerator
        :param document: existing opened document file, defaults to None
        :param filename: File to be opened, defaults to None
        :param syntax: Markdown syntax flavor (GitHub vs GitLab)
        :param root_object: Whether the instance of this class is root object, defaults to None
        :param tmp_dir: Path of temporal directory. NOTE: not in user, defaults to None
        """
        # Attribute for determining if object is first instance of Markdowngenerator
        self.root_object = root_object
        self.document = document
        self.document_data_array = document_data_array if document_data_array else []
        self.enable_write = enable_write
        self.enable_TOC = enable_TOC

        if not filename:
            self.filename = Path(DEFAULT_FILE_LOCATION).resolve()
            self.default_filename_on_use = True
        elif isinstance(filename, Path):
            self.filename = filename
            self.default_filename_on_use = False
        else:
            self.filename = Path(filename).resolve()
            self.default_filename_on_use = False
        self.syntax = syntax if syntax else "gitlab"

        # Trailing details, details section open but not ended if count > 0.
        self.unfinished_details_summary_count = {"value": 0}

        # Header information for table of contents
        self.header_info = header_data_array if header_data_array else []
        self.header_index = header_index if header_index else 0

        # Directory for tmp files, currently not in use.
        self.tmp_dir = tmp_dir

    def __enter__(self):
        """ Override enter method to enable usage of 'with' to open/close. """
        if self.filename.is_dir():
            self.filename.mkdir(exist_ok=True)
            self.filename.joinpath(DEFAULT_FILE_LOCATION, ".md")
            self.default_filename_on_use = True
        if not self.document:
            self.document = open(f"{self.filename}", "w+")
            current_tmp_dir = tempfile.gettempdir()
            self.tmp_dir = tempfile.TemporaryDirectory(dir=current_tmp_dir)
        return self

    def __exit__(self, *args, **kwargs):
        """ Close file on exit. """
        if self.enable_TOC:
            self.genTableOfContent()
        if not self.enable_write:
            self.document.writelines(self.document_data_array)
        self.document.close()

    def genTableOfContent(self, linenumber=TOC_LINE_POSITION, max_depth=3):
        """ Method for creating table of contents. """
        tableofcontents = []
        tableofcontents.append(f"### Table of Contents  {linesep}")
        prevLevel = 0
        padding = "  "
        for header in self.header_info:
            name = header.get("headerName")
            level = header.get("headerLevel")
            href = header.get("headerHref")
            if name and level and href:
                if level <= max_depth:
                    if prevLevel != 0 and prevLevel - level < -2:
                        level = prevLevel + 2

                    tableofcontents.append(
                        f"{level * padding}* {self.generateHrefNotation(name, href)}{linesep}"
                    )
                prevLevel = level
        tableofcontents.append(f"  {linesep}")
        self.document_data_array = (
            self.document_data_array[: linenumber - 1]
            + tableofcontents
            + self.document_data_array[linenumber - 1 :]
        )
        if self.enable_write:
            self.document.close()
            self.document = open(self.filename, "w")
            self.document.writelines(self.document_data_array)

    def writeText(self, text, html_escape: bool = True):
        """ Method for writing arbitrary text into the document file. """
        if html_escape:
            self.document_data_array.append(escape(str(text)))
            if self.enable_write:
                self.document.write(escape(str(text)))
            return
        self.document_data_array.append(str(text))
        if self.enable_write:
            self.document.write(str(text))

    def writeTextLine(self, text=None, html_escape: bool = True):
        """ Write arbitrary text into the document file and add new line. """
        if text is None:
            self.document_data_array.append(str("") + linesep)
            if self.enable_write:
                self.document.write(str("") + linesep)

            return
        if html_escape:
            self.document_data_array.append(escape(str(text)) + "" + linesep)
            if self.enable_write:
                self.document.write(escape(str(text)) + "" + linesep)
            return
        self.document_data_array.append(str(text) + "" + linesep)
        if self.enable_write:
            self.document.write(str(text) + "" + linesep)

    def writeAttributeValuePairLine(self, key_value_pair: tuple, total_padding=30):

        if len(key_value_pair) == 2:
            required_padding = total_padding - len(key_value_pair[0])
            self.writeTextLine(
                f"{self.addBoldedAndItalicizedText(key_value_pair[0])}{HTML_SPACE*required_padding}{key_value_pair[1]}"
            )
        else:
            return

    def addHeader(self, level: int, text):
        """ Method for adding named headers for the document. """
        # Text for lowercase, remove punctuation, replace whitespace with dashesh
        anchor = "#" + text.lower().translate(
            str.maketrans("", "", punctuation.replace("-", ""))
        ).replace(" ", "-")

        self.header_index += 1
        header = {"headerName": escape(text),
                  "headerLevel": level,
                  "headerHref": anchor,
                  "headerID": self.header_index}

        if level <= MAX_HEADER_LEVEL and level >= MIN_HEADER_LEVEL:
            if level != MIN_HEADER_LEVEL or self.header_index != 1:
                self.writeTextLine()
            self.writeTextLine(f"{level * HEADER} {text}")
        elif level < MIN_HEADER_LEVEL:
            header["headerLevel"] = MIN_HEADER_LEVEL
            self.writeTextLine(f"{MIN_HEADER_LEVEL * HEADER} {text}")
        else:
            header["headerLevel"] = MAX_HEADER_LEVEL
            # Add empty line before header unless it's level is 1 (default MIN)
            self.writeTextLine()
            self.writeTextLine(f"{MAX_HEADER_LEVEL * HEADER} {text}")

        self.header_info.append(header)

    def addBoldedText(self, text: str, write_as_line: bool = False) -> str:
        bolded = f"**{text.strip()}**"
        if write_as_line:
            self.writeTextLine(bolded)
        return bolded

    def addItalicizedText(self, text, write_as_line: bool = False) -> str:
        italicized = f"*{text.strip()}*"
        if write_as_line:
            self.writeTextLine(italicized)
        return italicized

    def addBoldedAndItalicizedText(self, text, write_as_line: bool = False) -> str:
        bolded_italicized = f"***{text.strip()}***"
        if write_as_line:
            self.writeTextLine(bolded_italicized)
        return bolded_italicized

    def addStrikethroughText(self, text, write_as_line: bool = False) -> str:
        if self.syntax not in ["gitlab", "github"]:
            raise AttributeError("GitLab and GitHub Markdown syntax only.")

        strikethrough = f"~~{text.strip()}~~"
        if write_as_line:
            self.writeTextLine(strikethrough)
        return strikethrough

    def generateHrefNotation(self, text, url, title=None) -> str:
        if title:
            return f'[{text}]({url} "{title}")'
        return f"[{text}]({url})"

    def generateImageHrefNotation(self, image_uri: str, alt_text, title=None) -> str:
        if title:
            return f'![{alt_text}]({image_uri} "{title}")'
        return f"![{alt_text}]({image_uri})"

    def addHorizontalRule(self):
        self.writeTextLine(f"{linesep}{HORIZONTAL_RULE}{linesep}")

    def addCodeBlock(self, text, syntax: str = None, escape_html: bool = False):
        # Escape backtics/grave accents in attempt to deny codeblock escape
        grave_accent_escape = "\`"

        text = text.replace("`", grave_accent_escape)

        if escape_html:
            self.writeTextLine(
                f"{CODE_BLOCK}{syntax}{linesep}{text}{linesep}{CODE_BLOCK}")
        else:
            self.writeTextLine(
                f"{CODE_BLOCK}{syntax}{linesep}{text}{linesep}{CODE_BLOCK}",
                html_escape=False,)

    def addInlineCodeBlock(self, text, escape_html=False, write=False):
        """ Method for adding highlighted code in inline style in Markdown. """
        inline_hl = f"{INLINE_CODE_HIGHLIGHT}{text}{INLINE_CODE_HIGHLIGHT}"
        if write:
            if escape_html:
                self.writeText(inline_hl)
            else:
                self.writeText(inline_hl, html_escape=False)
        else:
            return inline_hl

    def addSinglelineBlockQuote(self, text):
        """ Method for adding single line blockquote. """
        self.writeTextLine(
        f"{SINGLE_LINE_BLOCKQUOTE}{escape(text.strip())}", html_escape=False)

    def addUnorderedList(self, iterableStringList):
        """ Method from constructing unordered list. """
        for item in iterableStringList:
            self.writeText(f"  * {item}{linesep}")
        self.writeTextLine()

    def addTable(self, header_names = None, row_elements=None,
                 alignment="center", dictionary_list=None,
                 html_escape=True, capitalize_headers=False):
        """ Method for generating Markdown table with centered cells. """
        useDictionaryList = False
        useProvidedHeadernames = False

        if row_elements is None:
            if dictionary_list is None:
                raise TypeError(
                    f"Invalid paramaters for generating new table. \
                     Use either dictionary list or row_elements.")
            else:
                useDictionaryList = True

        if header_names:
            useProvidedHeadernames = True

        self.writeTextLine()
        if not useProvidedHeadernames and dictionary_list:
            try:
                header_names = dictionary_list[0].keys()
            except AttributeError as e:
                return
        try:
            for header in header_names:
                # Capitalize header names
                if capitalize_headers:
                    self.writeText(f"| {header.capitalize()} ")
                else:
                    self.writeText(f"| {header} ")
        except TypeError as e:
            return
        # Write ending vertical bar
        self.writeTextLine(f"|")
        # Write dashes to separate headers
        if alignment == "left":
            self.writeTextLine("".join(["|", ":---|" * len(header_names)]))
        elif alignment == "center":
            self.writeTextLine("".join(["|", ":---:|" * len(header_names)]))
        elif alignment == "right":
            self.writeTextLine("".join(["|", "---:|" * len(header_names)]))
        else:
            self.writeTextLine("".join(["|", ":---:|" * len(header_names)]))

        if not useDictionaryList:
            for row in row_elements:
                if len(row) > len(header_names):
                    continue
                for element in row:
                    # Check if element is list
                    # If it is, add it as by line by line into single cell
                    if isinstance(element, list):
                        self.writeText("| ")
                        for list_str in element:
                            self.writeText(list_str)
                            self.writeText("<br>", html_escape=False)
                    else:
                        self.writeText(f"| {element}", html_escape)

                self.writeTextLine(f"|")
        else:
            # Iterate over list of dictionaries
            for row in dictionary_list:
                for key in row.keys():
                    if isinstance(row.get(key), list):
                        self.writeText("| ")
                        for list_str in row.get(key):
                            self.writeText(list_str)
                            self.writeText("<br>", html_escape=False)
                    else:
                        self.writeText(f"| {row.get(key)}", html_escape)
                self.writeTextLine(f"|")
        self.writeTextLine()

    def insertDetailsAndSummary(self, summary_name="Click to collapse/fold.",
                                escape_html=True):
        self.writeTextLine("<details>", html_escape=False)
        if escape_html:
            self.writeTextLine(f"<summary>{escape(summary_name)}</summary>",
                               html_escape=False)
        else:
            # Makes bolding possible for summary name with HTML
            self.writeTextLine(f"<summary>{summary_name}</summary>",
                               html_escape=False)
        self.writeTextLine()
        self.unfinished_details_summary_count["value"] += 1

    def endDetailsAndSummary(self):
        self.writeTextLine()
        self.writeTextLine("</details>", html_escape=False)
        self.unfinished_details_summary_count["value"] -= 1
