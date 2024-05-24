HEADER = "#HEADERS"
PROMPTS = "#PROMPTS"
USEFUL_SEARCH_TERMS = "#USEFUL_SEARCH_TERMS"



    
def build_prompt(name, institution, requested):
    start = "When given the name '" + name + "' and the institution of" \
        " '" + institution + "', I want you to find the following data for the" \
        " individual. "

    end = " Output should be in JSON format. If you cannot find" \
        " information on a particular topic, enter 'NONE' for that field. Do not" \
        " include sub-JSONs or sub-lists."
    return start + requested + end


def read_saved(saved_path):
    """
    This takes a saved format text file and retrieves the important
    information. See below for an example of how these text files are
    set up.
    """
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

    saved_format = {"headers":  headers_to_use,
                    "prompts": prompts_to_use,
                    "search_terms": useful_search_terms}
    return saved_format

            
#saved = read_saved("saved_output_formats/scientometrics.txt")
#print("HEADERS")
#print(saved["headers"])
#print("PROMPTS")
#print(saved["prompts"])
#print("EXTRA SEARCH TERMS")
#print(saved["search_terms"])


# EXAMPLE_SAVED_FORMAT.txt
#  #HEADERS
#  ColA,ColB,ColC,ColD
#  #USEFUL_SEARCH_TERMS
#  researchgate,ieee
#  #PROMPTS
#  Given A, give me C
#  Given B, give me A
