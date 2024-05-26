import os
import main
import output_format
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGridLayout, QLineEdit, QFileDialog, QWidget,
    QPushButton, QTabWidget, QMessageBox, QVBoxLayout, QLabel, QComboBox,
    QPlainTextEdit, QScrollArea, QHBoxLayout, QInputDialog
    )
from PyQt6.QtGui import QPalette, QColor, QIcon
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal


class Worker(QObject):
    finished = pyqtSignal()
    to_log = pyqtSignal(str)
    def __init__(self, input_path, output_name, output_format):
        super().__init__()
        self.input_path = input_path
        self.output_name = output_name
        self.output_format = output_format

    def run(self):
        main.main(self.input_path, self.output_name, self.output_format,
                  self.to_log)
        self.finished.emit()


class TopChunk(QWidget):
    def __init__(self, parent, tab_chunk):
        super().__init__(parent)
        self.tab_chunk = tab_chunk

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


    def load_format(self):
        column_section = self.tab_chunk.column_section
        prompt_section = self.tab_chunk.prompt_section
        site_section = self.tab_chunk.site_section

        formatting = {"header": [],
                     "prompts": [],
                     "sites": []}

        for i in range(column_section.count()):
            curr = column_section.itemAt(i).widget()
            if isinstance(curr, QLineEdit) and curr.text() != "":
                formatting["header"].append(curr.text())

        if len(formatting["header"]) == 0:
            chosen_format = self.tab_chunk.drop_down.currentText()
            if chosen_format == self.tab_chunk.base_drop_down_text:
                chosen_format = "base"
            print(chosen_format)
            return output_format.read_saved(chosen_format)

        for i in range(prompt_section.count()):
            curr = prompt_section.itemAt(i).widget()
            if isinstance(curr, QPlainTextEdit) and curr.toPlainText() != "":
                formatting["prompts"].append(curr.toPlainText())

        if len(formatting["prompts"]) == 0:
            formatting["prompts"] = output_format.build_prompts(
                formatting["header"])

        for i in range(site_section.count()):
            curr = site_section.itemAt(i).widget()
            if isinstance(curr, QLineEdit) and curr.text() != "":
                formatting["sites"].append(curr.text())

        return formatting


    def process(self):
        path = self.input_filepath.text()
        file_name = os.path.basename(path)
        if os.path.exists(path) is False or \
        os.path.splitext(file_name)[-1].lower() != ".csv":
            message = "The input '" + path + "' is either nonexistant" \
                " or not a .csv"
            show_error_to_user(message)
            return

        output_name = self.output_name.text() 
        if len(output_name) == 0:
            output_name = os.path.splitext(file_name)[0] + "_output"
        output_name += ".xlsx"

        output_format = self.load_format()
        self.tab_chunk.log.setText("")

        self.thread = QThread()
        self.worker = Worker(path, output_name, output_format)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.to_log.connect(self.tab_chunk.add_log_text)
        self.thread.start()

        self.process_button.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.process_button.setEnabled(True)
        )

        dialog = QMessageBox(self)
        dialog.setWindowTitle("All done")
        dialog.setText("Scraping has been finished and is outputted to " +
                       output_name)
        self.thread.finished.connect(dialog.exec)



class TabChunk(QWidget):

    base_drop_down_text = "Load saved format"

    def __init__(self, parent):
        super().__init__(parent)

        self.saved_output_format_names = {}
        
        self.init_tabs()
        

    def init_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)
        self.tabs.setStyleSheet("background:white")

        self.init_table_tab()
        self.init_log_tab()
        self.init_alteration_tab()


    def init_table_tab(self):
        label = QLabel("Finish me, please")
        self.tabs.addTab(label, "Table")


    def init_log_tab(self):
        self.log = QLabel("Please GOD, finish me")
        self.log.setWordWrap(True)
        self.log.setOpenExternalLinks(True)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.log)
        self.tabs.addTab(scroll_area, "Log")


    def add_log_text(self, text):
        self.log.setText(self.log.text() + text)


    def init_alteration_tab(self):
        self.alter_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()

        # The four main sections of this tab
        self.header_section = QVBoxLayout()
        self.column_section = QVBoxLayout()
        self.prompt_section = QVBoxLayout()
        self.site_section = QVBoxLayout()

        saved_format_section = QHBoxLayout()
        # To add: a way to save and name current setups
        self.drop_down = QComboBox()
        self.update_output_format_names()
        self.drop_down.currentTextChanged.connect(self.load_format)
        saved_format_section.addWidget(self.drop_down)
        build_prompts = QPushButton("Generate prompts")
        build_prompts.clicked.connect(self.generate_prompts)
        save_format = QPushButton("Save formatting")
        save_format.clicked.connect(self.save_format)
        saved_format_section.addWidget(QLabel())
        saved_format_section.addWidget(save_format)
        saved_format_section.addWidget(QLabel())
        saved_format_section.addWidget(build_prompts)
        self.header_section.addLayout(saved_format_section)

        information = QLabel("This row is reserved for information, as well as" \
                             " access to the pdf (or whatever)")
        self.header_section.addWidget(information)

        self.alter_layout.addLayout(self.header_section)
        self.alter_layout.addLayout(self.column_section)
        self.alter_layout.addLayout(self.prompt_section)
        self.alter_layout.addLayout(self.site_section)

        self.base_alter_view()
        
        widget = QWidget()
        widget.setLayout(self.alter_layout)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(widget)
        self.tabs.addTab(self.scroll_area, "Alter output")


    def base_alter_view(self):
        # The below chunk initializes the first column input text box, and
        #  its corresponding button.
        self.add_column = QPushButton("Add output")
        self.add_column.clicked.connect(self.add_new_column_box)
        self.add_new_column_box()

        # The below chunk initializes the first prompt input box and its
        #  corresponding button.
        self.add_prompt = QPushButton("Add prompt")
        self.add_prompt.clicked.connect(self.add_new_prompt_box)
        self.add_new_prompt_box()

        # This chunk accomplishes the same as above, except for useful sites
        self.add_site = QPushButton("Add site")
        self.add_site.clicked.connect(self.add_new_site_box)
        self.add_new_site_box()


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


    def add_new_site_box(self):
        site_input = QLineEdit()
        site_input.setPlaceholderText("Enter useful sites to scrape")
        self.site_section.addWidget(site_input)
        self.site_section.addWidget(self.add_site)
        return site_input


    def load_format(self):
        self.clear_layout(self.column_section)
        self.clear_layout(self.prompt_section)
        self.clear_layout(self.site_section)

        if self.drop_down.currentText() == self.base_drop_down_text:
            self.base_alter_view()
            return

        current_text = self.drop_down.currentText()
        if current_text == "":
            return
        path = self.saved_output_format_names[self.drop_down.currentText()]
        saved = output_format.read_saved(path)

        for h in saved["header"]:
            current = self.add_new_column_box()
            current.setText(h)
        for p in saved["prompts"]:
            current = self.add_new_prompt_box()
            current.setPlainText(p)
        for s in saved["sites"]:
            current = self.add_new_site_box()
            current.setText(s)


    def save_format(self):
        header = []
        prompts = []
        sites = []

        for i in range(self.column_section.count()):
            curr = self.column_section.itemAt(i).widget()
            if isinstance(curr, QLineEdit) and curr.text() != "":
                header.append(curr.text())

        if len(header) == 0:
            show_error_to_user("There are no output columns set")
            return
        
        for i in range(self.prompt_section.count()):
            curr = self.prompt_section.itemAt(i).widget()
            if isinstance(curr, QPlainTextEdit) and curr.toPlainText() != "":
                prompts.append(curr.toPlainText())

        if len(prompts) == 0:
            prompts = output_format.build_prompts(header)

        for i in range(self.site_section.count()):
            curr = self.site_section.itemAt(i).widget()
            if isinstance(curr, QLineEdit) and curr.text() != "":
                sites.append(curr.text())

        name, ok = QInputDialog().getText(self, "Format name", "Enter a name" \
                                          " for the new format")
        if name and ok:
            to_save = {"header": header,
                       "prompts": prompts,
                       "sites": sites,
                       "name": name}
            output_format.save_format(to_save)
            self.update_output_format_names()
        else:
            return


    def generate_prompts(self):
        columns = []
        for i in range(self.column_section.count()):
            curr = self.column_section.itemAt(i).widget()
            if isinstance(curr, QLineEdit) and curr.text() != "":
                columns.append(curr.text())           

        if len(columns) == 0:
            return

        prompts = output_format.build_prompts(columns)
        self.clear_layout(self.prompt_section)
        for p in prompts:
            current = self.add_new_prompt_box()
            current.setPlainText(p)
        

    def clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            layout.itemAt(i).widget().setParent(None)


    def update_output_format_names(self):
        viable_paths = [f for f in os.listdir(output_format.SAVED_FOLDER) \
                        if os.path.splitext(f)[-1].lower() == ".txt"]

        # Every key is the name, excluding .txt, and every value is the
        #  path
        self.saved_output_format_names = {os.path.splitext(name)[0] \
                                          : output_format.SAVED_FOLDER + "/" \
                                          + name for name in viable_paths}

        self.drop_down.clear()
        self.drop_down.addItems([self.base_drop_down_text] + \
                           list(self.saved_output_format_names.keys()))

        
class UserInterface(QMainWindow):

    COL_MAX = 4

    def __init__(self):
        super().__init__()

        self.init_base_aesthetics()
        #self.init_tabs()


    def init_base_aesthetics(self):
        self.setWindowTitle("VT-ARC Scraping Tool")
        #self.setWindowIcon(QIcon("data/vtarc_logo.png"))
        self.layout = QGridLayout()

        tab_chunk = TabChunk(self)
        self.layout.addWidget(tab_chunk.tabs, 2, 2, 3, 3)

        top_chunk = TopChunk(self, tab_chunk)
        self.layout.addWidget(top_chunk.input_filepath, 0, self.COL_MAX - 1,
                              Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(top_chunk.input_filepath_button, 0, self.COL_MAX,
                              Qt.AlignmentFlag.AlignLeft)
        
        self.layout.addWidget(top_chunk.output_name, 1, self.COL_MAX - 1,
                              Qt.AlignmentFlag.AlignRight)

        self.layout.addWidget(top_chunk.process_button, 1, self.COL_MAX,
                              Qt.AlignmentFlag.AlignLeft)

        container = QWidget()
        container.setLayout(self.layout)
        container.setStyleSheet("background:rgb(150,50,30)")
        self.setCentralWidget(container)
        self.resize(800, 600)


def show_error_to_user(message):
    dialog = QMessageBox()
    dialog.setWindowTitle("Error")
    dialog.setText(message)
    dialog.exec()
    # possibly use QMessageBox
    print(message)

app = QApplication([])
window = UserInterface()
window.show()

app.exec()
