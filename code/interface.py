import main
import os
import output_format
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGridLayout, QLineEdit, QFileDialog, QWidget,
    QPushButton, QTabWidget, QMessageBox, QVBoxLayout, QLabel, QComboBox,
    QPlainTextEdit, QScrollArea, QHBoxLayout
    )
from PyQt6.QtGui import QPalette, QColor, QIcon
from PyQt6.QtCore import Qt


# The main GUI is laid out using QGridLayout, these are the max dimensions
ROW_MAX = 4
COL_MAX = 4


class TopChunk(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.init_top_chunk()

    
    def init_top_chunk(self):
        self.input_filepath = QLineEdit()
        self.input_filepath.setStyleSheet("background:white")
        self.input_filepath.setPlaceholderText("Input file path")

        self.output_name = QLineEdit()
        self.output_name.setStyleSheet("background:white")
        self.output_name.setPlaceholderText("Output file name")

        self.input_filepath_button = QPushButton("Choose input file")
        self.input_filepath_button.setStyleSheet("background:white")
        self.input_filepath_button.clicked.connect(self.get_filename)

        self.process_button = QPushButton("Process!")
        self.process_button.setStyleSheet("background:white")
        self.process_button.clicked.connect(self.process)


    def get_filename(self):
        file_filter = 'Data File (*.csv)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.path.expanduser("~"),
            filter=file_filter
        )
        self.input_filepath.insert(str(response[0]))


    def process(self):
        path = self.input_filepath.text()
        file_name = os.path.basename(path)
        if os.path.exists(path) is False or \
        os.path.splitext(file_name)[-1].lower() != ".csv":
            message = "The input '" + path + "' is either nonexistant" \
                " or not a .csv"
            self.show_error_to_user(message)
            return

        output_name = self.output_name.text() 
        if len(output_name) == 0:
            output_name = os.path.splitext(file_name)[0] + "_output"
        output_name += ".xlsx"

        self.process_button.setEnabled(False)
        main.main(path, output_name)
        dialog = QMessageBox(self)
        dialog.setWindowTitle("All done")
        dialog.setText("Scraping has been finished and is outputted to " +
                    output_name)
        dialog.exec()
        self.process_button.setEnabled(True)


class TabChunk(QWidget):

    output_format_folder = "saved_output_formats"
    base_drop_down_text = "Load saved format"

    def __init__(self, parent):
        super().__init__(parent)

        self.saved_output_format_names = {}
        self.update_output_format_names()
        
        self.init_tabs()
        

    def init_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)
        self.tabs.setStyleSheet("background:white")

        self.init_log_tab()
        self.init_table_tab()
        self.init_alteration_tab()


    def init_table_tab(self):
        label = QLabel("Finish me, please")
        self.tabs.addTab(label, "Table")


    def init_log_tab(self):
        label = QLabel("Please GOD, finish me")
        self.tabs.addTab(label, "Log")


    def init_alteration_tab(self):
        self.alter_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()

        # The three main sections of this tab
        self.header_section = QVBoxLayout()
        self.column_section = QVBoxLayout()
        self.prompt_section = QVBoxLayout()

        saved_format_section = QHBoxLayout()
        # To add: a way to save and name current setups
        self.drop_down = QComboBox()
        self.drop_down.addItems([self.base_drop_down_text] + \
                           list(self.saved_output_format_names.keys()))
        self.drop_down.currentTextChanged.connect(self.load_format)
        saved_format_section.addWidget(self.drop_down)
        self.header_section.addLayout(saved_format_section)

        information = QLabel("This row is reserved for information, as well as" \
                             " access to the pdf (or whatever)")
        self.header_section.addWidget(information)

        self.alter_layout.addLayout(self.header_section)
        self.alter_layout.addLayout(self.column_section)
        self.alter_layout.addLayout(self.prompt_section)

        self.base_output_prompt()
        
        widget = QWidget()
        widget.setLayout(self.alter_layout)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(widget)
        self.tabs.addTab(self.scroll_area, "Alter output")


    def base_output_prompt(self):
        # The below chunk initializes the first column input text box, and
        #  its corresponding button.
        column_input = QLineEdit()
        column_input.setPlaceholderText("Enter column outputs")
        self.column_section.addWidget(column_input)
        self.add_column = QPushButton("Add output")
        self.add_column.clicked.connect(self.add_new_column_box)
        self.column_section.addWidget(self.add_column)

        # The below chunk initializes the first prompt input box and its
        #  corresponding button.
        prompt_input = QPlainTextEdit()
        prompt_input.setPlaceholderText("If no prompt is inputted, the" \
                                        " default option will be used")
        self.prompt_section.addWidget(prompt_input)
        self.add_prompt = QPushButton("Add prompt")
        self.add_prompt.clicked.connect(self.add_new_prompt_box)
        self.prompt_section.addWidget(self.add_prompt)


    def add_new_column_box(self):
        column_input = QLineEdit()
        column_input.setPlaceholderText("Enter column outputs")
        self.column_section.addWidget(column_input)
        self.column_section.addWidget(self.add_column)
        return column_input


    def add_new_prompt_box(self):
        prompt_input = QPlainTextEdit()
        prompt_input.setPlaceholderText("If no prompt is inputted, the" \
                                        " default option will be used")
        self.prompt_section.addWidget(prompt_input)
        self.prompt_section.addWidget(self.add_prompt)
        return prompt_input


    def load_format(self):
        self.clear_layout(self.column_section)
        self.clear_layout(self.prompt_section)

        if self.drop_down.currentText() == self.base_drop_down_text:
            self.base_output_prompt()
            return

        path = self.saved_output_format_names[self.drop_down.currentText()]
        saved = output_format.read_saved(path)

        for h in saved["headers"]:
            current = self.add_new_column_box()
            current.setText(h)
        for p in saved["prompts"]:
            current = self.add_new_prompt_box()
            current.setPlainText(p)
        #for s in saved["search_terms"]:
        #    current = self.add_new_search_box()
        #    current.setText(s)


    def clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)


    def update_output_format_names(self):
        viable_paths = [f for f in os.listdir(self.output_format_folder) \
                        if os.path.splitext(f)[-1].lower() == ".txt"]

        # Every key is the name, excluding .txt, and every value is the
        #  path
        self.saved_output_format_names = {os.path.splitext(name)[0] \
                                          : self.output_format_folder+"/"+name
                                          for name in viable_paths}

        
class UserInterface(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_base_aesthetics()
        #self.init_tabs()


    def init_base_aesthetics(self):
        self.setWindowTitle("VT-ARC Scraping Tool")
        #self.setWindowIcon(QIcon("data/vtarc_logo.png"))
        self.layout = QGridLayout()

        top_chunk = TopChunk(self)
        self.layout.addWidget(top_chunk.input_filepath, 0, COL_MAX - 1,
                              Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(top_chunk.input_filepath_button, 0, COL_MAX,
                              Qt.AlignmentFlag.AlignLeft)
        
        self.layout.addWidget(top_chunk.output_name, 1, COL_MAX - 1,
                              Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(top_chunk.process_button, 1, COL_MAX,
                              Qt.AlignmentFlag.AlignLeft)


        tab_chunk = TabChunk(self)
        self.layout.addWidget(tab_chunk.tabs, 2, 2, 3, 3)

        container = QWidget()
        container.setLayout(self.layout)
        container.setStyleSheet("background:rgb(150,50,30)")
        self.setCentralWidget(container)
        self.resize(800, 600)


    def show_error_to_user(self, message):
        # possibly use QMessageBox
        print(message)


app = QApplication([])
window = UserInterface()
window.show()

app.exec()
