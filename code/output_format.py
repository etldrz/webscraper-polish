HEADER = "#HEADER"
PROMPTS = "#PROMPTS"
USEFUL_SEARCH_TERMS = "#USEFUL_SEARCH_TERMS"

SAVED_FOLDER = "saved_output_formats"
DEFAULT_NAME = "scientometrics (default).txt"
DEFAULT_PATH = SAVED_FOLDER + "/" + DEFAULT_NAME
    
RESERVED_COLUMNS = ["email", "emails", "Email", "Emails",
                    "Other key notes", "other key notes",
                    "Relevant links", "relevant links",
                    "Name", "name",
                    "Institution", "institution"]


def build_prompts(columns):
    col_count = len(columns)
    optim_prompt_size = 3
    
    start = "When given the name 'PERSON_NAME' and the institution of" \
        " 'INSTITUTION_NAME', I want you to find the following data for the" \
        " individual: "

    end = " Output should be in JSON format. If you cannot find" \
        " information on a particular topic, enter 'NONE' for that field. Do not" \
        " include sub-JSONs or sub-lists."

    for r in RESERVED_COLUMNS:
        if r in columns:
            ind = columns.index(r)
            del columns[ind]
            if r.lower() == "other key notes":
                columns += ["Patents under their name", "Awards recieved"]

    prompts = []

    if len(columns) == 0:
        return ["NONE"]
        
    if col_count < optim_prompt_size:
        requested = "'" + "', '".join(columns) + "'."
        prompts.append(start + requested + end)
        return prompts
    rem = col_count % optim_prompt_size
    while len(columns) > 0:
        rem -= 1
        upper = 3 + (rem > 0)
        requested = "'" + "', '".join(columns[0:upper]) + "'."
        prompts.append(start + requested + end)
        del columns[0:upper]
    return prompts


def read_saved(saved_path):
    """
    This takes a saved format text file and retrieves the important
    information. See below for an example of how these text files are
    set up.
    """

    if saved_path == "base":
        saved_path = DEFAULT_PATH
    headers_to_use = []
    prompts_to_use = []
    useful_search_terms = []

    with open(saved_path) as f:
        line = f.readline()
        while line:
            if HEADER in line:
                # Moving it along to get the line below
                line = f.readline()
                headers_to_use = line.split("\n")[0].split(",")
            elif USEFUL_SEARCH_TERMS in line:
                line = f.readline()
                useful_search_terms = line.split("\n")[0].split(",")
            elif PROMPTS in line:
                lines = f.readlines()
                prompts_to_use = [prompt.split("\n")[0] for prompt in lines]
            line = f.readline()

    saved_format = {"header":  headers_to_use,
                    "prompts": prompts_to_use,
                    "sites": useful_search_terms}
    return saved_format


def save_format(to_save):
    """
    Where to_save is a dict containing
    'header': output headers
    'sites': additional sites, if any
    'prompts': prompts to use
    'name': the name of the saved format
    """
    to_write = SAVED_FOLDER + "/" + to_save["name"] + ".txt"

    with open(to_write, 'w') as f:
        f.write(HEADER + "\n")
        f.write(",".join(to_save["header"]) + "\n")
        f.write(USEFUL_SEARCH_TERMS + "\n")
        f.write(",".join(to_save["sites"]) + "\n")
        f.write(PROMPTS + "\n")
        f.write("\n".join(to_save["prompts"]))


# EXAMPLE_SAVED_FORMAT.txt
#  #HEADERS
#  ColA,ColB,ColC,ColD
#  #USEFUL_SEARCH_TERMS
#  researchgate,ieee
#  #PROMPTS
#  Given A, give me C
#  Given B, give me A
