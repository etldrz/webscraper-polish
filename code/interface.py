import main
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGridLayout, QLineEdit, QFileDialog, QWidget,
    QPushButton, QTabWidget, QMessageBox
    )
from PyQt6.QtGui import QPalette, QColor, QIcon
from PyQt6.QtCore import Qt


# The main GUI is laid out using QGridLayout, these are the max dimensions
ROW_MAX = 4
COL_MAX = 4


class UserInterface(QMainWindow):
    def __init__(self):
        super().__init__()

        self.init_base_aesthetics()
        self.init_input_chunk()
        self.init_tabs()


    def init_base_aesthetics(self):
        self.setWindowTitle("VT-ARC Scraping Tool")
        #self.setWindowIcon(QIcon("data/vtarc_logo.png"))
        self.layout = QGridLayout()
        container = QWidget()
        container.setLayout(self.layout)
        container.setStyleSheet("background:rgb(212,211,217)")
        self.setCentralWidget(container)
        self.resize(800, 600)


    def init_input_chunk(self):
        self.input_filepath = QLineEdit()
        self.input_filepath.setPlaceholderText("Input file path")

        self.output_name = QLineEdit()
        self.output_name.setPlaceholderText("Output file name")

        self.input_filepath_button = QPushButton("Choose input file")
        self.input_filepath_button.clicked.connect(self.get_filename)

        self.process_button = QPushButton("Process!")
        self.process_button.clicked.connect(self.process)

        self.layout.addWidget(self.input_filepath, 0, COL_MAX - 1,
                              Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(self.input_filepath_button, 0, COL_MAX,
                              Qt.AlignmentFlag.AlignLeft)
        
        self.layout.addWidget(self.output_name, 1, COL_MAX - 1,
                              Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(self.process_button, 1, COL_MAX,
                              Qt.AlignmentFlag.AlignLeft)


    def init_tabs(self):
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.North)
        tabs.setMovable(False)
        self.layout.addWidget(tabs, 2, 2, 3, 3)
        
        for i in range(1, 4):
            tabs.addTab(QPushButton(str(i)), str(i))


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
        

    def show_error_to_user(self, message):
        # possibly use QMessageBox
        print(message)


app = QApplication([])
window = UserInterface()
window.show()

app.exec()
