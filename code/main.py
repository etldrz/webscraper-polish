from bs4 import BeautifulSoup
from user_agents import user_agents
from openpyxl import Workbook, load_workbook
import random
import requests
import csv
import time
import tiktoken
import analysis
import pandas as pd
import numpy as np

bad_link_prefixes = ["/search", "q=", "/?",
                     "/advanced_search"]

bad_locations = ["facebook", "instagram",
                 "linkedin", "twitter", "ratemyprofessors",
                 "coursicle", "youtube", "amazon",
                ".doc", ".pdf", "wiki", "imgres"]

agent = random.choice(user_agents)

#agent = "Mozilla%2F5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537" + \
#    ".36+(KHTML%2C+like+Gecko)+Chrome%2F90.0.4430.85+Safari%2F537" + \
#    ".36+RuxitSynthetic%2F1.0+v7014856858959599523+t4743487995012709438" + \
#    "+ath1fb31b7a+altpriv+cvcv%3D2+smf%3D0"

to_search = []

output_path = "name.xlsx"


def build_output_file(file_path):
    """
    This builds the sheet, adds the relevant column names,
    then openpyxl.load_workbook() will be called to append
    new researchers as they are scraped and processed.
    """
    header = ["Name", "Last Name", "Institution", "Title", "Domain", "Gender",
              "Topic", "Research Focus", "Expertise", "Research Fields",
              "Other Key Notes", "Relevant Links", "Email", "Website"]
    wb = Workbook()
    ws = wb.active
    ws.append(header)
    wb.save(file_path)


def read_csv(file_path):
    """
    Reads some csv and loads each researcher as a dict into the list to_search.
    """
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        # The file has a header
        next(reader)

        for researcher in reader:

            # If the domain is not included
            if len(researcher) == 2:
                researcher.append("N/A")

            to_search.append({"Name": researcher[0],
                              "Institution": researcher[1],
                              "Domain": researcher[2]})
    return


def get_links(researcher):
    """
    Gets relevant links from the first page of a google search for some researcher.
    """
    query = researcher['Name'] + " " + researcher['Institution']
    researchgate_query = query + " resarchgate"
    ieee_query = query + " ieee"

    links = []

    search_url = f"https://www.google.com/search?q={query}"
    search_url_researchgate = f"https://www.google.com/search?q={researchgate_query}"
    search_url_ieee = f"https://www.google.com/search?q={ieee_query}"

    req = requests.get(search_url, agent)
    time.sleep(np.random.poisson(1.2, 1)[0])
    researchgate_req = requests.get(search_url_researchgate, agent)
    time.sleep(np.random.poisson(1.2, 1)[0])
    ieee_req = requests.get(search_url_ieee, agent)

    print(req)
    print(researchgate_req)
    print(ieee_req)
    print(type(req.content))
    bs = BeautifulSoup(req.content + researchgate_req.content + ieee_req.content, 'html.parser')
    # Select every single <a> element
    raw_links = bs.select("a")
    # Filter links that do not contain "google.com" or start with the prefixes defined.
    # Iterating through a set of links because there may be many values of the same because
    #  it searches three different times
    filtered_links = [link['href'] for link in raw_links
                      if not any(link['href'].startswith(prefix)
                                 or link['href'].find('google.com') > 0
                                 for prefix in bad_link_prefixes)]

    # Filter links that don't contain searches
    filtered_links = [link for link in filtered_links
                      if not any(link.find(search) > -1
                                 for search in bad_locations)]

    # Only grab the relevent part of the link if it includes more in it
    links += [link.split("/url?q=")[-1].split("&sa")[0]
              for link in filtered_links]

    links = [link for link in links if "/search" not in link]

    full_name = researcher['Name'].lower().split(" ")
    first_name = full_name[0]
    last_name = full_name[-1]
    institution = researcher['Institution']
    # links = list(filter(check, links, item))
    links = [link for link in map(lambda x: x.lower(), set(links))
             if "ieee" in link
             or "researchgate" in link and (first_name in link and last_name in link)
             or (first_name in link and last_name in link)
             or institution.lower() in link]

    ## NEED SOME SORT OF CHECK FOR TOKENS ##

    return links


def write_to_excel(output_path, researcher):
    """
    Writes each researcher to excel by using the package openpyxl.

    How it works is it checks the pre-written Excel sheet for header names (see
    build_output_file() and finds the corresponding key in the researcher dict
    that is passed to this funciton. The value for that key is then put into
    a list of length equal to the number of needed columns at the index corresponding
    to the column with the same name. After all of the keys and columns are matched
    up, the list is appended to the workbook and the workbook is closed.

    In this way, only needed columns are saved, and the workbook is updated after each
    reseaercher.
    """

    wb = load_workbook(output_path, data_only=True)
    ws = wb.active
    # getting the column names 
    header = ws[1]

        
    to_write = ["NONE"]*len(header)

    #bugged out, bc to_search is a list (not the dreaded triple loop!)
    for key in researcher['output']:
        for h in header:

            col = h.column
            if h.internal_value.lower() == "relevant links":
                to_write[col - 1] = "\n".join(researcher['Links used'])
                continue 

            data = researcher['output'][key]
            items = data.split("\n")
            count = 0
            while count < (len(items) - 1) and items[0] == "":
                del items[0]
                count = count + 1
            unique = "\n".join(set(items))

            if h.internal_value.lower() == key.lower():
                # minus one because col counts the row count of an excel file
                data = researcher['output'][key]

                #items = list(filter(lambda x: ratio))

                if unique == "":
                    unique = "NONE"
                to_write[col - 1] = unique 
            elif h.internal_value.lower() == "topic":
                to_write[col - 1] = ""
                
    
    #for r in to_search:
    #    to_write.append(r['output'])
    #df = pd.dataframe(to_write)
    #name = "completed.xlsx"
    #df.to_excel(name, engine='openpyxl')
    ws.append(to_write)
    wb.save(output_path)


def bigmode(input_path):
    """
    for some csv formatted correctly (ie has a header and is filled with researchers,
    their institutions, and their domains) this will get good links, then
    use analysis.py to gather the webtext and have gpt analyze it.

    At the end, a single researcher dict will have the following
      Name: ...,
      Institution: ...,
      Domain: ...,
      Links used: all the good links found by get_links(),
      output: the output created by analysis.gogo(), as a sub-dict. Note that the links
        used are also within this sub-dict.

    After all this is compiled, the found output will be written to the excel file.
    """

    # Just in case
    to_search.clear()

    read_csv(input_path)
    build_output_file(output_path)

    client = analysis.animate_client()

    for researcher in to_search:
        researcher['Links used'] = get_links(researcher)

        # If no good links are found, then
        if len(researcher['Links used']) == 0:
            researcher['output'] = analysis.bad_output("no links found :/")

        print("======================")
        print(researcher['Name'] + " " + researcher['Institution'] + " " + researcher['Domain'])
        print('')
        print("There were " + str(len(researcher['Links used'])) + " links found.")
        print(researcher['Links used'])

        researcher['output'] = analysis.gogo(researcher, client)
        print('')
        print(researcher['output'])
        print('')
        write_to_excel(output_path, researcher)

    return


def token_data(file_path):
    """
    This is used for testing purposes/cost analysis. It
    will gather and ouput the tokens needed per researcher 
    """
    to_search.clear()

    read_csv(file_path)

    encoding = tiktoken.encoding_for_model(analysis.CLIENT_MODEL)

    all_tokens = []
    for r in to_search:
        r['Links used'] = get_links(r)

        time.sleep(1)

        webtext = ""
        for l in r['Links used']:
            webtext += analysis.get_webtext(l)
        if webtext == "":
            r['Token input'] = 0
            all_tokens.append(0)

        # using tiktoken, the token count of all of the
        #   webtext used per researcher will be gathered
        #   (tiktoken is the official openai token counter
        #   (tokens are how openai charges))
        tokens = len(encoding.encode(webtext)) * 3
        # add the token count of the prompts to the token count of input
        tokens += len(encoding.encode(
            "".join(analysis.build_prompts(
                r['Name'], r['Institution']))))
        r['Token input'] = tokens
        all_tokens.append(tokens)

        print(r['Name'])
        print(r['Institution'])
        print(r['Links used'])
        print("Number of links found: " + str(len(r['Links used'])))
        print('')
        print("Tokens needed for input: " + str(r['Token input']))
        print("========================================")

    print("The sample mean, with " + str(len(all_tokens)) +
          " individuals, is:")
    print(sum(all_tokens) / len(all_tokens))
    return


#token_data("test_input/embree.csv")
bigmode("test_input/embree.csv")
