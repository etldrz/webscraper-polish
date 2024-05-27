import random
import requests
import csv
import time
import tiktoken
import pandas as pd
import numpy as np
import output_format
import analysis
from bs4 import BeautifulSoup
from user_agents import user_agents
from openpyxl import Workbook, load_workbook

bad_link_prefixes = ["/search", "q=", "/?",
                     "/advanced_search"]

bad_locations = ["facebook", "instagram",
                 "linkedin", "twitter", "ratemyprofessors",
                 "coursicle", "youtube", "amazon",
                ".doc", ".pdf", "wiki", "imgres"]


#agent = "Mozilla%2F5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537" + \
#    ".36+(KHTML%2C+like+Gecko)+Chrome%2F90.0.4430.85+Safari%2F537" + \
#    ".36+RuxitSynthetic%2F1.0+v7014856858959599523+t4743487995012709438" + \
#    "+ath1fb31b7a+altpriv+cvcv%3D2+smf%3D0"


def build_output_file(file_path, header):
    """
    This builds the sheet, adds the relevant column names,
    then openpyxl.load_workbook() will be called to append
    new researchers as they are scraped and processed.
    """
    #header = ["Name", "Last Name", "Institution", "Title", "Domain", "Gender",
    #          "Topic", "Research Focus", "Expertise", "Research Fields",
    #          "Other Key Notes", "Relevant Links", "Email", "Website"]
    wb = Workbook()
    ws = wb.active
    ws.append(list(map(lambda x: x.capitalize(), header)))
    wb.save(file_path)


def read_csv(file_path, table):
    """
    Reads some csv and loads each researcher as a dict into the list to_search.
    """
    to_search = []
    for_table = ""
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)


        for person in reader:
            person_data = {header[i].lower() : person[i] \
                              for i in range(0,len(header))}
            person_data['header'] = list(map(lambda x: x.lower(), header))

            to_search.append(person_data)
            for_table += person_data["name"] + "," \
                + person_data["institution"] + "*"

    table.emit(for_table)
    return to_search


def get_links(person, sites, agent, log):
    """
    Gets relevant links from the first page of a google search for some person.
    """
    query = person['name'] + " " + person['institution']

    links = []

    search_url = f"https://www.google.com/search?q={query}"
    all_search = [search_url + " " + site for site in sites]
    all_search = [search_url] + all_search

    log.emit("<b>Initial search links used:</b><br>")
    to_log = [f"<a href=\"{site}\">{site}</a>" for site in all_search]
    log.emit("<br>".join(to_log) + "<br><br>")
    content = []
    for search in all_search:
        req = requests.get(search, agent)
        content.append(req.content)

    bs = BeautifulSoup(b''.join(content), 'html.parser')
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

    full_name = person['name'].lower().split(" ")
    first_name = full_name[0]
    last_name = full_name[-1]
    institution = person['institution']
    # links = list(filter(check, links, item))
    links = [link for link in map(lambda x: x.lower(), set(links))
             if "ieee" in link
             or "researchgate" in link and (first_name in link and last_name in link)
             or (first_name in link and last_name in link)
             or institution.lower() in link]

    ## NEED SOME SORT OF CHECK FOR TOKENS ##


    return links


def write_to_excel(output_path, person, log):
    """
    Writes each person to excel by using the package openpyxl.

    How it works is it checks the pre-written Excel sheet for header names (see
    build_output_file() and finds the corresponding key in the person dict
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
    for key in person['output']:
        for h in header:

            col = h.column
            if h.internal_value.lower() == "relevant links":
                to_write[col - 1] = "\n".join(person['links used'])
                continue 

            data = person['output'][key]
            items = data.split("\n")
            count = 0
            while count < (len(items) - 1) and items[0] == "":
                del items[0]
                count = count + 1
            unique = "\n".join(set(items))

            if h.internal_value.lower() == key.lower():
                # minus one because col counts the row count of an excel file
                data = person['output'][key]

                #items = list(filter(lambda x: ratio))

                if unique == "":
                    unique = "NONE"
                to_write[col - 1] = unique 
            elif h.internal_value.lower() == "topic":
                to_write[col - 1] = ""
                
    
    ws.append(to_write)
    wb.save(output_path)
    log.emit("<br><br><b>Saved to excel output.</b><br>")


def main(input_path, output_name, output_format, log, table):
    """
    For some csv formatted correctly (ie has a header and is filled with
    researchers, their institutions, and their domains) this will get
    good links, then use analysis.py to gather the webtext and have gpt
    analyze it.

    At the end, a single researcher dict will have the following
      Name: ...,
      Institution: ...,
      Domain: ...,
      Links used: all the good links found by get_links(),
      output: the output created by analysis.analyze(), as a sub-dict.
        Note that the links used are also within this sub-dict.

    After all this is compiled, the found output will be written to the excel
    file.
    """

    to_search = read_csv(input_path, table)
    log.emit("<h2>Starting scraping on " + str(len(to_search)) + \
             " individuals.</h2><br><br><b>OUTPUT HEADER:</b><br>" + \
             ", ".join(output_format["header"]) + "<br>")
    for i in range(len(output_format["prompts"])):
        log.emit("<br><b>PROMPT " + str(i + 1) + "</b><br>")
        log.emit(output_format["prompts"][i] + "<br>")
    if len(output_format['sites']) >= 0:
        log.emit("<br><b>ADDITIONAL SEARCH TERMS:</b><br>" + \
                 ", ".join(output_format['sites']) + "<br>")

    build_output_file(output_name, output_format["header"])

    client = analysis.animate_client()

    count = 0
    for person in to_search:
        start = time.time()
        log.emit("<br><h3>Scraping " + person['name'] + ", " + \
                 person["institution"] + "</h3><br><br>")

        agent = random.choice(user_agents)
        person["links used"] = get_links(person, output_format["sites"], agent,
                                         log)
        log.emit("<b>Sites found: ")
        # If no good links are found, then
        if len(person['links used']) == 0:
            log.emit("N/A</b><br>")
            person['output'] = analysis.bad_output("no links found :/")
        else:
            log.emit(str(len(person["links used"])) + "</b><br>")
            log.emit("<br>".join([f"<a href=\"{site}\">{site}</a>" \
                                  for site in person["links used"]]))

        person["output"] = analysis.analyze(person, client,
                                            output_format["prompts"])

        write_to_excel(output_name, person, log)
        end = time.time()
        log.emit("<b>Time spent: " + str(round(end - start, 2)) + " s</b>")
        table.emit("completed:" + str(count))
        count += 1
    return


def token_data(file_path):
    """
    This is used for testing purposes/cost analysis. It will gather and ouput
    the tokens needed per researcher 
    """
    to_search.clear()

    read_csv(file_path)

    encoding = tiktoken.encoding_for_model(analysis.CLIENT_MODEL)

    all_tokens = []
    for r in to_search:
        r['Links used'] = get_links(r)

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
