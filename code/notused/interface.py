import sys, threading, asyncio, time, os
from PyQt5.QtWidgets import QApplication, QWidget, \
    QLabel, QLineEdit, QPushButton, QFileDialog, QFrame
from PyQt5.QtGui import QIcon, QFont, QPixmap
from WebScraping import WebScraping
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
#import logger_config


class WebScraperGUI(QWidget):


    def __init__(self):
        # Inherit Widget methods
        super().__init__()

        self.web_scraping = WebScraping()
        #self.wb = WebScraping()

        #Create the widget layouts
        self.hbox = QHBoxLayout()
        self.vbox = QVBoxLayout() 
        
        #Set background color of the widget
        self.setStyleSheet("background-color: rgb(50,50,50);")
 
        self.title = 'Virginia Tech Applied Research Corporation: Web Scraper'
        self.left = 500
        self.top = 250
        self.width = 1750
        self.height = 1250
        self.initUI()
        self.input_path = ""
        
        self.update_timer = QTimer(self)  # Create a QTimer instance
        self.update_timer.timeout.connect(self.refresh_timers)  # Connect the timer to the refresh function
        self.update_timer.start(1000)
        

    def initUI(self):
        """
        This deals with the basic layout of the GUI.
        """
        
        self.setWindowTitle(self.title)
        
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowIcon(QIcon('./data/VTARClogo.png'))
       
        # Create a decorative black frame on the top side of window
        self.top_blk_frame = QFrame(self)
        self.top_blk_frame.resize(self.width, 175)
        self.top_blk_frame.setStyleSheet("background-color: rgb(30,30,30)")
        
        # Create a decorative black frame on the left side of window
        self.left_blk_frame = QFrame(self)
        self.left_blk_frame.resize(500, self.height)
        self.left_blk_frame.setStyleSheet("background-color: rgb(20,20,20)")
    

        # Set VT-ARC logo to be in the top left corner
        self.logo_label = QLabel(self)
        self.logo_label.move(20,10)
        self.logo_label.resize(475, 200)
        arc_logo = QPixmap('./data/VTARClogo.png')
        self.logo_label.setPixmap(arc_logo)
        self.logo_label.setStyleSheet("background-color: rgb(20,20,20);")

        # Creates the Input File text label
        self.file_input_label = QLabel(self)
        self.file_input_label.setText('File Input:')
        self.file_input_label.setFont(QFont('Times', 12))
        self.file_input_label.setStyleSheet("color: rgb(255, 255, 255);"
                                            " background-color: rgb(30,30,30);")
        self.file_input_label.move(int(self.width/2) - 250, 30)
        self.file_input_label.resize(175, 50)

        # Create File name text label
        self.name_input_label = QLabel(self)
        self.name_input_label.setText('File Name:')
        self.name_input_label.setFont(QFont('Times', 12))
        self.name_input_label.setStyleSheet("color: rgb(255, 255, 255);" +
                                            " background-color: rgb(30,30,30);")
        self.name_input_label.move(int(self.width/2) - 250, 85)
        self.name_input_label.resize(175, 50)

        # Creates the text box to enter a file
        self.input_entry = QLineEdit(self)
        self.input_entry.move(800, 35)
        self.input_entry.resize(450, 40)
        self.input_entry.setStyleSheet("color: rgb(255, 255, 255);")
        
        # Creates text box for file name
        self.name_input_entry = QLineEdit(self)
        self.name_input_entry.move(800, 90)
        self.name_input_entry.resize(450, 40)
        self.name_input_entry.setStyleSheet("color: rgb(255, 255, 255);")

        # Button for user to select file
        self.input_button = QPushButton('Select File', self)
        self.input_button.setFont(QFont('Times', 12))
        self.input_button.setStyleSheet("color: rgb(255, 255, 255);")
        self.input_button.move(1300, 35)
        self.input_button.resize(175, 50)
        self.input_button.clicked.connect(self.select_input_file)
        #self.input_button.clicked.connect(self.initialize_logger)
    
        # Button to run the tool
        self.process_button = QPushButton('Process', self)
        self.process_button.setFont(QFont('Times', 12))
        self.process_button.setStyleSheet("color: rgb(255, 255, 255);")
        self.process_button.move(1500, 35)
        self.process_button.resize(175, 50)
        self.process_button.clicked.connect(self.save_input_name)
        # Where the file starts to process
        self.process_button.clicked.connect(self.process_csv) 
        
        # Scraping Progress
        self.process_label = QLabel("Status: ", self)
        self.process_label.setFont(QFont('Times', 12))
        self.process_label.setStyleSheet("color: rgb(255, 255, 255);" +
                                         " background-color: rgb(20,20,20);")
        self.process_label.move(30, 550)
        self.process_label.resize(300, 50)

        # Current progress for status label
        self.status_label = QLabel(self)
        self.status_label.setFont(QFont('Times', 12))
        self.status_label.setStyleSheet("color: rgb(255, 255, 255);" +
                                        " background-color: rgb(20, 20, 20)")
        self.status_label.move(135, 550)
        self.status_label.resize(200, 50)

        # Number of Researchers being Processed
        self.stat1 = QLabel("Total Reseachers: ", self)
        self.stat1.setFont(QFont('Times', 12))
        self.stat1.move(30, 325)
        self.stat1.resize(400, 50)
        self.stat1.setStyleSheet("color: rgb(255, 255, 255);" +
                                 " background-color: rgb(20, 20, 20)")

        # Processing time
        self.stat3 = QLabel("Total Time", self)
        self.stat3.setFont(QFont('Times', 12))
        self.stat3.move(30, 475)
        self.stat3.resize(400, 50)
        self.stat3.setStyleSheet("color: rgb(255, 255, 255);" +
                                 " background-color: rgb(20, 20, 20)")
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)  # Three columns for data
        self.table.setHorizontalHeaderLabels(['Name', 'Institution', 'Time'])
        header_font = QFont('Times', 11, QFont.Bold)
        self.table.horizontalHeader().setFont(header_font)
        self.table.verticalHeader().setFont(header_font)
        self.table.setFixedSize(800, 600)  # Set fixed size for the table
        self.table.setStyleSheet("color: rgb(30, 30, 30);" +
                                 " background-color: rgb(255, 255, 255); border-radius: 10px;")
        self.table.horizontalHeader().setDefaultSectionSize(255)

        # Create the main layout which is vertical
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(600, 100, 100, 50)  # Adding some padding around the layout

        # Add the table directly to the main layout without centering spacers
        main_layout.addWidget(self.table, alignment=Qt.AlignCenter)  # Add table aligned to the top

        # Set the main layout to the widget
        self.setLayout(main_layout)
        


    #def initialize_logger(self):
    #    """
    #    Initializes a new logger, and is called when the file is processed.
    #    """
    #    logger_config.setup_logger()
    

    def save_input_name(self):
        time_stamp = datetime.now().strftime('%m-%d-%Y_%H%M')
        
        # Get the name input from the user (if any)
        default_file_name = os.path.splitext(os.path.basename(self.input_entry.text()))[0]
        
        # Get the name input from the user (if any)
        file_name_input = self.name_input_entry.text()
        
        # Use the default file name if no input is given
        if not file_name_input.strip():
            file_name_input = default_file_name + '_output'
        
        file_name_input = file_name_input + '_'+ time_stamp
        
        # Saves the file name for the file
        with open('file_name.txt', 'w') as f:
            f.write(file_name_input)
    


    def reset(self):
        
        while self.table.rowCount() > 0:
            self.table.removeRow(0)

 
    def update(self, wb):
        
        self.num_candidate = len(wb.researchers_scraped)
        self.table.setRowCount(self.num_candidate)
        count = 0
        
        for researcher in wb.researchers_scraped:
            name = researcher.researcher_data['Name']
            institution = researcher.researcher_data['Institution']

            # Set the name and institution
            self.table.setItem(count, 0, QTableWidgetItem(name))
            self.table.setItem(count, 1, QTableWidgetItem(institution))
            
            # Initialize the timer column with zero seconds
            self.table.setItem(count, 2, QTableWidgetItem("0s"))

            count += 1

    def refresh_timers(self):
        
        current_time = time.time()
        
        for row in range(self.table.rowCount()):
            name = self.table.item(row, 0).text() if self.table.item(row, 0) else ""
            researcher = next((r for r in self.web_scraping.researchers_scraped if r.researcher_data['Name'] == name), None)
            
            if researcher:
                timestamps = researcher.researcher_time.get(name, [])
                start_time = timestamps[0] if timestamps else current_time
                end_time = timestamps[1] if len(timestamps) > 1 else current_time

                elapsed_time = end_time - start_time
                hours, remainder = divmod(int(elapsed_time), 3600)
                minutes, seconds = divmod(remainder, 60)
                time_str = f"{hours}h {minutes}m {seconds}s"
                self.table.item(row, 2).setText(time_str)


   

    def select_input_file(self):
        
        input_path, _ = QFileDialog.getOpenFileName(self, 'Select File', '', 'CSV Files (*.csv)')
        
        if input_path:
            self.input_path = input_path
            self.web_scraping.set_input_name(self.input_path)
            self.input_entry.setText(self.input_path)


    def process_csv(self):
        """
        Where the processing of names initiates.
        """
        
        input_path = self.input_path   
        process = threading.Thread(target=self.async_process_handler)
        process.start()
        self.process_button.setEnabled(False)
        self.status_label.setText("Processing")


    def async_process_handler(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        task = loop.create_task(self.process_csv_thread(self.input_path)) 
        loop.run_until_complete(task)
        loop.close()



    async def process_csv_thread(self, input_path):
        self.start_time = time.time()
        wb = WebScraping()
        wb.read_csv(input_path)
        
        researcher_count = len(wb.researchers_scraped)        
        self.stat1.setText(f"Total Researchers: {researcher_count}")
        self.stat1.setFont(QFont('Times', 10))

        elapsed_timer = threading.Thread(target=self.thread_elapsed_time)
        elapsed_timer.start()
        self.reset()
        self.update(wb)
        
        await self.web_scraping.run()
        
        self.process_button.setEnabled(True)
        self.status_label.setText("Complete")


    def thread_elapsed_time(self):
        """
        Disables the process button while scraping and determines
        the elapsed time to process the individuals
        """
        while (self.process_button.isEnabled() == False):
            time.sleep(1)
            self.stat3.setText(f"Running Time: {(time.time() - self.start_time):.0f} secs")
            self.stat3.setFont(QFont('Times', 10))
        
        self.stat3.setText(f"Completed Time: {(time.time() - self.start_time):.0f} secs")
   

class Worker(QThread):
    update_signal = pyqtSignal(int, str)

    def __init__(self, row, start_time, end_time=None):
        super().__init__()
        self.row = row
        self.start_time = start_time
        self.end_time = end_time

    def run(self):
        while True:
            current_time = time.time()
            if self.end_time and current_time >= self.end_time:
                elapsed_time = self.end_time - self.start_time
                self.update_signal.emit(self.row, f"{elapsed_time:.2f} seconds")
                break
            else:
                elapsed_time = current_time - self.start_time
                self.update_signal.emit(self.row, f"{elapsed_time:.2f} seconds")
            time.sleep(1)  # Sleep for a second before updating again   




if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WebScraperGUI()
    ex.show()
    sys.exit(app.exec_())
