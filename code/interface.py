import main
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGridLayout, QLineEdit, QFileDialog, QWidget,
    QPushButton, QTabWidget, QMessageBox, QVBoxLayout, QLabel, QComboBox,
    QPlainTextEdit
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

        tab_titles = ["Table", "Log", "Alter output"]
        
        for t in tab_titles:
            match t:
                case "Table":
                    self.init_table_tab()
                case "Log":
                    self.init_log_tab()
                case "Alter output":
                    self.init_alteration_tab()
            #layout = QVBoxLayout()
            #layout.addWidget(QLineEdit())
            #layout.addWidget(QPushButton("SHIT."))
            #widget = QWidget()
            #widget.setLayout(layout)
            #tabs.addTab(widget, str(i))


    def init_table_tab(self):
        label = QLabel("Finish me, please")
        self.tabs.addTab(label, "Table")


    def init_log_tab(self):
        label = QLabel("Please GOD, finish me")
        self.tabs.addTab(label, "Log")


    def init_alteration_tab(self):
        alter_layout = QGridLayout()

        drop_down = QComboBox()
        default_message = "Choose saved format"
        drop_down.addItems([default_message] + list(self.saved_output_format_names.keys()))
        alter_layout.addWidget(drop_down, 0, 0,
                               Qt.AlignmentFlag.AlignLeft)


        information = QLabel("This row is reserved for information, as well as" \
                             " access to the pdf (or whatever)")
        alter_layout.addWidget(information, 1, 0)
        

        prompt_input = QPlainTextEdit()
        prompt_input.setPlaceholderText("If no prompt is inputted, the" \
                                        " default option will be used")
        alter_layout.addWidget(prompt_input, 2, 0)
        add_prompt = QPushButton("Add prompt")
        add_prompt.clicked.connect(self.add_new_prompt_box)
        alter_layout.addWidget(add_prompt, 2, 1)
        

        widget = QWidget()
        widget.setLayout(alter_layout)
        self.tabs.addTab(widget, "Alter output")


    def add_new_prompt_box(self):
        print("hello")


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
        container.setStyleSheet("background:rgb(212,211,217)")
        self.setCentralWidget(container)
        self.resize(800, 600)


    def show_error_to_user(self, message):
        # possibly use QMessageBox
        print(message)


app = QApplication([])
window = UserInterface()
window.show()

app.exec()
