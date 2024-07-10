# Basics of getting the tool up and running

1. Clone or download the `main` branch of this repository.
1. Download the requirements (`pip install -r requirements.txt`). It is recommended to do this inside of a [virtual environment](https://www.freecodecamp.org/news/how-to-setup-virtual-environments-in-python/).
1. Put the API key for OpenAI into an environment file: `./.env` as `OPENAI_API_KEY=...`
1. The command `python code/interface.py` will initiate the GUI, as well as the rest of the code.
1. From here, all that needs to be done is load the file (using the GUI's buttons) and press 'Process'.

The tool requires that input data be formatted in the following manner (as a .csv). A header line is always required, and the input MUST contain a column labeled `Name` and a column labeled `Institution`. Additional columns can be included, these additional columns will be included in the output but won't be used in the internal workings of the tool.

| Name | Institution | Domain |
| ---- | ----------- | ------ |
| Santa Claus | Toy Factory | Industry |
	
Output will be in the form of an Excel file (.xlsx) containing all output that the tool was able to get. There is an information pdf in the docs file, also accessible through the GUI.
