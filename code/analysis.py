from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from user_agents import user_agents
from dotenv import load_dotenv
from openai import OpenAI
import requests
import os
import random
import re
import json

agent = random.choice(user_agents)

# this model is cheaper than gpt 4, still gives good output, and has json mode.
CLIENT_MODEL = "gpt-3.5-turbo-1106"


def animate_client():
    """
    Gives an instance of an active openai client.
    """
    load_dotenv()
    client = OpenAI()
    client.api_key = os.getenv("OPENAI_API_KEY")
    return client


def get_webtext(link, log):
    """
    Gets the text of some webpage located at the given URL (the URL has
    to be good). The returned text is sans html/css. If the text-getting
    fails, an empty string is returned.
    """
    try:
        with sync_playwright() as p:
            brow = p.chromium.launch(slow_mo=50)
            page = brow.new_page(user_agent=agent)
            page.goto(link)
            bs = BeautifulSoup(page.content(), "html.parser")
            webtext = bs.get_text().replace('\n', '').replace(
                '"', '').replace("\xa0", '').strip()
        return webtext
    except Exception as e:
        log.emit("<br>The webtext of " + link + " could not be gotten<br><br>")
        return ""

##### MAKE SURE TO CHECK FOR OPENAI ERRORS, SEE https://github.com/openai/openai-python
def generate_response(client, prompt_list, webtext, person, log):
    """
    Gets a response item from an openai client based off of text from some website
    and a given prompt. If the response-getting fails, bad_output() is returned.
    """

    output = {}
    for prompt in prompt_list:
        prompt = prompt.replace("PERSON_NAME", person['name'])
        prompt = prompt.replace("INSTITUTION_NAME", person['institution'])
        try:
            response = client.chat.completions.create(
                model = CLIENT_MODEL,
                messages = [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": webtext}
                ]
            )

            # openai will return a dictionary if the response fails on their
            #   end for some reason.
            if isinstance(response, dict):
                log.emit("<br><br><br>GPT failed to properly analyze the current"\
                         " webtext. Here is OpenAI's reasoning:<br>" \
                         + str(response))
            # else, if the response is good, return the text gpt generated
            #   as a dictionary (additional checks are preformed
            #   by this function).
            else:
                as_dict = conv_to_dict(response.choices[0].message.content,
                                       person)
                output = as_dict
        except Exception as e:
            log.emit("<br><br><br>GPT failed to properly analyze the current" \
                     " webtext. Here is OpenAI's reasoning:<br>" + str(e)) 
            output = bad_output(e)

    return output


def bad_output(err):
    """
    To be used when there is no good output for some researcher, either
    because of bad/no links, or the gpt output fails for some reason. 
    It returns a dict containing whatever error causes the transformation of
    GPT's output to fail.
    """
    output = {
        "error": err
    }
    return output


def conv_to_dict(json_string, researcher):
    """
    Converts a JSON string to a python dict. The JSON string in question
    is from gpt, so there are two seperate try/catches to try and subvert
    bad/incorrect output.
    """

    try:
        as_dict = json.loads(json_string)
        return as_dict
    except:
        print("asdfadsf")
        ######################

    # If the output fails for this basic check, the first assumption is that
    # the output may be in code format, ie 
    # ```json
    # GPT output
    # ```
    #
    # To that end, the string is converted to a list split by "\n".
    # Then, the fist and last items of the list are deleted.
    # If this fails, then a dict created by bad_output is returned
    try:
        fixed_chat = json_string.split("\n")
        del fixed_chat[0]
        del fixed_chat[-1]
        as_dict = json.loads("\n".join(fixed_chat))
        return as_dict
    except Exception as e:
        return bad_output(e) 


def combine_dicts(to_combine):
    # Replaces any instance of "NONE" with a blank string, for easy combining
    cleaned = [{key: "" if value == "NONE" else value
                for key, value in current.items()}
               for current in to_combine]

    # Combines all the values of the same keys together
    total = {}
    for clean in cleaned:
        for key, value in clean.items():
            if key in total:
                # To prevent double adding of basic values, like name or
                #   institution, as well as to prevent blank lines being added
                if total[key] == value or \
                   value == "":
                    continue
                total[key] += "\n" + str(value)
            else:
                total[key] = str(value)

    return total


def get_email(webtext, link):
    agent = random.choice(user_agents)
    try:
        req = requests.get(link, agent)
    except:
        print("THERE WAS AN ERROR IN GET_EMAIL")
        return []
    bs = BeautifulSoup(req.content, 'html.parser')

    anchors = bs.select("a")
    to_analyze = [txt.string for txt in anchors \
                  if txt.string is not None]
    to_analyze = " ".join(to_analyze)
    matches = re.findall(r'[\w+.\d-]*@[\w+.-]*', to_analyze)
    return matches


def analyze(person, client, prompts, need_email, log):
    """
    When given a researcher dict and an instance of an openai client, this
    will return a fully completed dict with all of the needed output. If
    there is no good output for some reason, this will return a dict created
    by bad_output().
    """
    skip_gpt = prompts[0] == "NONE"
    all_output = [{h : person[h.lower()]} for h in person['headers']]

    for link in person['links used']:
        webtext = get_webtext(link, log)
        if need_email:
            all_output.append({"email": get_email(webtext, link)})
        if not skip_gpt:
            all_output.append(generate_response(client, prompts, webtext,
                                                person, log))

    output = combine_dicts(all_output)
    return output
