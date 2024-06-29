import os
import main
import output_format
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QGridLayout, QLineEdit, QFileDialog, QWidget,
    QPushButton, QTabWidget, QMessageBox, QVBoxLayout, QLabel, QComboBox,
    QPlainTextEdit, QScrollArea, QHBoxLayout, QInputDialog, QTableWidget,
    QTableWidgetItem
    )
from PyQt6.QtGui import QPalette, QColor, QIcon, QPixmap
from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal


class Worker(QObject):
    """
    Used to deal with threading the scraping process. Threads are used so
    that the GUI is still opperable during scraping.

    Attributes:
     input_path: the path to the input csv file
     output_name: the path/name of the output Excel file
     output_format: a dict containing values needed for analysis, including
      header: the headers that the Excel file is to be built with
      sites: additional search terms to use for each person
      prompts: prompts that are to be fed to openai

    Class variables:
     finished: a pyqtSignal() that is used to determine if the scraping process
      is over
     encountered_error: a pyqtSignal() that is used to determine if an error
      is encountered while scraping. This is used to ensure that the process
      exits safely
     to_log: a pyqtSignal(str) that is used to update the GUI's log
     to_table: a pyqtSignal(str) that is used to update the GUI's table

    Methods:
     run: will call main.main() and give all necessary parameters. also deals
      with whether the process finishes properly or aborts early via pyqtSignals()
     __init__: Constructs all necessary attributes for run() to use
    """
    
    finished = pyqtSignal()
    encountered_error = pyqtSignal()
    to_log = pyqtSignal(str)
    to_table = pyqtSignal(str)


    def __init__(self, input_path, output_name, output_format):
        super().__init__()
        self.input_path = input_path
        self.output_name = output_name
        self.output_format = output_format


    def run(self):
        result = main.main(self.input_path, self.output_name,
                           self.output_format, self.to_log, self.to_table)
        # result will return nothing if main exits normally. False otherwise
        if result is None:
            self.finished.emit()
        else:
            self.encountered_error.emit()


class TopChunk(QWidget):
    """
    Initializes the top chunk of the GUI, above the tab chunk.

    Attributes:
     parent: the parent widget
     tab_chunk: the active TabChunk being used by the GUI

    Methods:
     init_top_chunk: creates the input path text box and button, as well as
      the output name text box and process button
     get_filename: pulls up a pop-up to navigate the directory and fetch the
      path of a csv file. Hooked up to the 'Input file path' button. Fills
      the filepath text-box input once some file is chosen.
     process: determines the output file name, and uses the Worker class to
      run main.main(). Displays dialog boxes at the end of running, based on
      whether or not the process closed with errors.
     load_format: retrieves the data from the 'Alter output' tab in the GUI and
      returns it as a dict
     __init__: calls init_top_chunk and sets tab_chunk  to self
    """

    def __init__(self, parent, tab_chunk):
        super().__init__(parent)
        self.tab_chunk = tab_chunk

        self.init_top_chunk()

    
    def init_top_chunk(self):
        """
        Each of the four chunks will add an additional button or text box to the
        GUI.
        """

        # text box for the file path
        self.input_filepath = QLineEdit()
        self.input_filepath.setStyleSheet("background:white")
        self.input_filepath.setPlaceholderText("Input file path")

        # text box for the output name. If no name is chosen, then the output
        #  will be the name of the input file + '_output.xlsx'
        self.output_name = QLineEdit()
        self.output_name.setStyleSheet("background:white")
        self.output_name.setPlaceholderText("Output file name")

        # a button to chose the input file. If clicked, it will fill the input
        #  text box with the appropriate string
        self.input_filepath_button = QPushButton("Choose input file")
        self.input_filepath_button.setStyleSheet("background:white")
        self.input_filepath_button.clicked.connect(self.get_filename)

        # a button to start the scrapping process
        self.process_button = QPushButton("Process!")
        self.process_button.setStyleSheet("background:white")
        self.process_button.clicked.connect(self.process)


    def get_filename(self):
        """
        Opens up a directory navigator, which will select for csv files.
        """

        file_filter = 'Data File (*.csv)'
        response = QFileDialog.getOpenFileName(
            parent=self,
            caption='Select a file',
            directory=os.path.expanduser("~"),
            filter=file_filter
        )

        # sets the text of the input file with the choice
        self.input_filepath.insert(str(response[0]))


    def process(self):
        """
        Will start the scrapping process, after first checking that the input
        is appropriate. If there is not output name chosen by the user, then
        this will create one.
        """

        # checks to see if the input file is good to use, ie that it exists and
        #  that it is a csv file
        path = self.input_filepath.text()
        file_name = os.path.basename(path)
        # if the conditions are not met, a dialog box will be displayed to the
        #  user
        if os.path.exists(path) is False or \
        os.path.splitext(file_name)[-1].lower() != ".csv":
            message = "The input '" + path + "' is either nonexistant" \
                " or not a .csv"
            show_error_to_user(message)
            return

        # checks to see if an output name was set by the user. If not, then
        #  the output name will be the name of the input file + '_output'
        output_name = self.output_name.text() 
        if output_name == "":
            output_name = os.path.splitext(file_name)[0] + "_output"
        output_name += ".xlsx"

        # gets all the necessary data from the 'Alter output' tab.
        output_format = self.load_format()

        # clears the log
        self.tab_chunk.log.setText("")

        # creates the thread and Worker to be used for this process instance
        self.thread = QThread()
        self.worker = Worker(path, output_name, output_format)
        self.worker.moveToThread(self.thread)
        
        # hooks up important events to the starting and ending of the thread.
        #  if errors are encountered, worker.encounter_error will be pinged
        #  and if the program finished successfully, woker.finished will be
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.encountered_error.connect(self.thread.quit)
        self.worker.encountered_error.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.to_log.connect(self.tab_chunk.add_log_text)
        self.worker.to_table.connect(self.tab_chunk.set_table_values)
        self.thread.start()

        # disables the process button until processing is complete
        self.process_button.setEnabled(False)
        self.thread.finished.connect(
            lambda: self.process_button.setEnabled(True)
        )

        # this will display if the tool finished successfully
        dialog = QMessageBox(self)
        dialog.setWindowTitle("All done")
        dialog.setText("Scraping has been finished and is outputted to " +
                       output_name)
        self.worker.finished.connect(dialog.exec)

        # this will display if the tool does not finish successfully
        error_dialog = QMessageBox(self)
        error_dialog.setWindowTitle("Error")
        error_dialog.setText("Scraping had to halt unexpectedly;" \
                             " output may or may not have been" \
                             " generated. Check the log for more" \
                             " information.")
        self.worker.encountered_error.connect(error_dialog.exec)


    def load_format(self):
        """
        Used to get pertinent data from the 'Alter output' tab. Returns as a
        dict
        """

        # each of these three is a widget containing different sections of the
        #  tab
        column_section = self.tab_chunk.column_section
        prompt_section = self.tab_chunk.prompt_section
        site_section = self.tab_chunk.site_section

        # for each section, the inputted details are gotten and put into this
        #  dict. Note that if a saved format is loaded, then the data of 'Alter
        #  output' will be filled
        formatting = {'header': [],
                     'prompts': [],
                     'sites': []}

        # for each in the number of widgets in this section, get the text if
        #  the widget is a QLineEdit object
        for i in range(column_section.count()):
            curr = column_section.itemAt(i).widget()
            if isinstance(curr, QLineEdit) and curr.text() != "":
                formatting['header'].append(curr.text())

        #if len(formatting['header']) == 0:
        #    chosen_format = self.tab_chunk.drop_down.currentText()
        #    if chosen_format == self.tab_chunk.base_drop_down_text:
        #        chosen_format = "base"
        #    return output_format.read_saved(chosen_format)

        # same as above, except QPlainTextEdit instead of QLineEdit
        for i in range(prompt_section.count()):
            curr = prompt_section.itemAt(i).widget()
            if isinstance(curr, QPlainTextEdit) and curr.toPlainText() != "":
                formatting["prompts"].append(curr.toPlainText())

        #if len(formatting["prompts"]) == 0:
        #    formatting["prompts"] = output_format.build_prompts(
        #        formatting["header"])

        for i in range(site_section.count()):
            curr = site_section.itemAt(i).widget()
            if isinstance(curr, QLineEdit) and curr.text() != "":
                formatting["sites"].append(curr.text())

        return formatting


class TabChunk(QWidget):
    """
    Deals with the tab chunk of the GUI.

    Atttribute:
     parent: the parent widget

    Class variables:
     base_drop_down_text: what is displayed in the drop down when the
      'Alter output' tab is empty

    Methods:
     init_tabs: creates and calls functions for each tab
     init_table_tab: deals with creating the table
     set_table_values: called whenever the table needs to be updated
     def_init_log_tab: creates the log
     add_log_text: adds text to the log. Text is formatted using basic HTML
     init_alteration_tab: builds the tab used to change and select the output
      format to be used for scraping
     base_alter_view: the bare-bones view that is applied to the alteration tab
      when either the base_drop_down_text is selected in the drop down, or the
      GUI first starts up
     add_new_column_box: adds a new box in the output column section. Used to
      set up the alteration tab, and add new input options when the 'Add output'
      button is clicked
     add_new_prompt_box: same as above, except for prompts
     add_new_site_box: same, except for sites
     load_format: triggered when the drop down menu has a new option selected.
      it will take the user's choice, find the corresponding txt file, and
      load in the format into the alteration tab.
     save_format: saves the current format using the selected name (chosen in
      a dialog box) in a text file in ./saved_output_formats/
     generate_prompts: this will automatically add prompts (overwritting any
      already there) to the prompt section of the alteration tab. see
      output_format.py for how these prompts are made.
     clear_layout: resets the alteration layout to base
     update_output_format_names: sets the values of the dropdown box in the
      alteration tab with the current saved format names
     __init__: sets the parent widget, creates an empty dict to contain output
      formats and calls init_tabs
    """

    base_drop_down_text = "Enter new format"

    def __init__(self, parent):
        super().__init__(parent)

        self.saved_output_format_names = {}
        
        self.init_tabs()
        

    def init_tabs(self):
        """
        Creates the base layout of the tab portion of the GUI
        """
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)
        self.tabs.setStyleSheet("background:white")

        # builds the basics of each tab
        self.init_alteration_tab()
        self.init_table_tab()
        self.init_log_tab()


    def init_table_tab(self):
        """
        Creates the basic layout of the table tab, using a QTableWidget object.
        The table has three columns and will have a number of rows equal to the
        amount of people being scraped. The table is centered through an
        extremely hacky method, but so it goes.
        """
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        header = ["Person", "Institution", "Completed?"]
        self.table.setHorizontalHeaderLabels(header)

        # centering the table using empty space
        layout = QHBoxLayout()
        buffer_count = 18
        for i in range(buffer_count):
            layout.addWidget(QLabel())
        layout.addWidget(self.table)
        for i in range(buffer_count):
            layout.addWidget(QLabel())

        # creating a widget to hold the layout
        table_tab_widget = QWidget()
        table_tab_widget.setLayout(layout)

        # making sure that the table can be scrolled through if the number
        #  of people is larger than what the screen can hold
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(table_tab_widget)

        self.tabs.addTab(table_tab_widget, "Table")


    def set_table_values(self, info):
        """
        This is updated when the Worker class variable table is pinged.
        Each time the scraping script pings table, it sends in a string that
        is encoded via specific deliminators.
        A ping letting the table know that a specific person has been scrapped
        and saved would be
         completed:ROW_NUM
        where ROW_NUM is the row number corresponding to the name/institution
        of the finished person.
        Building the table is done via a string like
         NAME1,INSTITUTION1*NAME2,INSTITUTION2
        with each name/institution found in the input csv file.

        info: the string being analyzed
        """

        if "completed" in info:
            row = int(info.split(":")[-1])
            curr_completed = self.table.setItem(row, 2, QTableWidgetItem("Yes"))
        else:
            # '*' is used as a splitter between each researcher being scraped
            #  while ',' is used as a splitter between the name and the
            #  institution.
            people = [person.split(",") for person in info.split("*")]

            # there will always be an empty array at the end 
            del people[-1]

            # fills the table
            self.table.setRowCount(len(people))
            for r in range(len(people)):
                for c in range(len(people[r])):
                    self.table.setItem(r, c, QTableWidgetItem(people[r][c]))
                    self.table.setItem(r, 2, QTableWidgetItem("No"))
            

    def init_log_tab(self):
        """
        Initializes an empty QLabel to be the log, that has a QScrollArea
        """

        self.log = QLabel("")
        self.log.setWordWrap(True)
        self.log.setOpenExternalLinks(True)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.log)
        self.tabs.addTab(scroll_area, "Log")


    def add_log_text(self, text):
        """
        Updates the log

        text: the text to add to the log
        """

        self.log.setText(self.log.text() + text)


    def init_alteration_tab(self):
        """
        
        """

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

        if os.path.exists(path):
            saved = output_format.read_saved(path)
        else:
            show_error_to_user("It looks like the selected format is no" \
                               " longer available for some reason; it could" \
                               " have been deleted or moved.")
            index = self.drop_down.findText(self.drop_down.currentText())
            self.drop_down
            self.drop_down.removeItem(index)
            self.load_format()
            return

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
                                          + name \
                                          for name in viable_paths}

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
        self.layout.addWidget(tab_chunk.tabs, 4, 0, 4, 5)

        #logo = QPixmap("data/vtarc_logo.png")
        #label = QLabel()
        #label.setPixmap(logo)
        #self.layout.addWidget(label, 0, 0, 2, 2)

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

        #container.setStyleSheet("background:black")
        container.setStyleSheet("background:rgb(20,20,20)")
        #container.setStyleSheet("background:rgb(150,50,30)")
        self.setCentralWidget(container)
        self.resize(800, 600)


def show_error_to_user(message):
    dialog = QMessageBox()
    dialog.setWindowTitle("Error")
    dialog.setText(message)
    dialog.exec()

app = QApplication([])
window = UserInterface()
window.show()
app.exec()
