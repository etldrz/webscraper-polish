# TODO:
## general
- have gui give some indication when job complete (including when user doesn't have it on screen)
- <em><strong>remember to go through your submitted instructions and try it through the eyes of someone who has nothing installed</strong></em>
- <em><strong>`pip freeze > requirements.txt`</strong></em>
## prompt change
- blacks out when tools is processing (or something similar)
- links to pdf doc that explains what a good prompt is
- in said doc have it mention
  a. the blocked sites
  b. the reserved column names ('Other Key Notes', 'Reserved Links', 'Email')
## log
- have GUI give option to save log as .txt
- have log record every notable event that occurs (success/failures/choices that the tool makes)

===========================
# Basics of getting the tool up and running

1. Clone or download the `Merged-Code` branch of this repository.
1. Download the requirements (`pip install -r requirements.txt`). It is recommended to do this inside of a [virtual environment](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/).
1. The command `python interface.py` will initiate the GUI, as well as the rest of the code.
1. From here, all that needs to be done is load the file (using the GUI's buttons) and press 'Process'.

Each run of the tool will create a log file, where bug information and additional data can be found.

The tool requires that input data be formatted in the following manner (as a .csv). A header line is always required, and the tool requires that input be in the order 'Name, Institution, Domain'.

| Name | Institution | Domain |
| ---- | ----------- | ------ |
| Santa Claus | Toy Factory | Industry |
	
Output will be in the form of an Excel file (.xlsx) containing all output that the tool was able to get.
