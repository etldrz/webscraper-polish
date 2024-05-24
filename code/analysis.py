from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from user_agents import user_agents
import os
import random
from dotenv import load_dotenv
from openai import OpenAI
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


def get_webtext(link):
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
        print(e)
        return ""


#def build_prompts(full_name, institution):
#    """
#    Builds three seperate prompts for GPT to analyze. Each prompt is flanked by
#    base_prompt/end_prompt.
#    """
#
#    base_prompt = "When given the name '" + full_name + "' and the institution of" \
#        " '" + institution + "', I want you to find the following data for the individual."
#
#    end_prompt = " If you can find nothing, still output the JSON in the desired format," \
#        " with 'NONE' in every category. Output should be in JSON format. If you cannot" \
#        " find information on a particular topic, enter 'NONE' for that field." \
#        " Do not include sub-JSONs or sub-lists."
#
#    prompta = base_prompt + \
#        " 'Email', 'Title', 'Gender', 'Research fields'." \
#        " Infer their gender from input." \
#        + end_prompt
#
#    promptb = base_prompt + \
#        " 'Research focus', 'Expertise'" \
#        + end_prompt
#
#    promptc = base_prompt + \
#        " 'Patents under their name', 'Awards received'" \
#        + end_prompt
#
#    return [prompta, promptb, promptc]


def generate_response(client, prompt_list, webtext, person):
    """
    Gets a response item from an openai client based off of text from some website
    and a given prompt. If the response-getting fails, bad_output() is returned.
    """

    #output = {"Name": researcher['Name'],
    #          "Institution": researcher['Institution'],
    #          "Domain": researcher['Domain']}
    output = {h : person[h] for h in person['header']}

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
                output = output | bad_output(str(response))
                print(bad_output((str(response))))
            # else, if the response is good, return the text gpt generated
            #   as a dictionary (additional checks are preformed
            #   by this function).
            else:
                as_dict = conv_to_dict(response.choices[0].message.content,
                                       person)
                output = output | as_dict
        except Exception as e:
            print(e)
            output = output | bad_output(e)

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
        print("original transform to dict failed")

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


def analyze(person, client, prompts):
    """
    When given a researcher dict and an instance of an openai client, this
    will return a fully completed dict with all of the needed output. If
    there is no good output for some reason, this will return a dict created
    by bad_output().
    """

    #prompt_list = build_prompts(person['name'], person['institution'])

    all_output = []
    for link in person['links used']:
        webtext = get_webtext(link)
        all_output.append(generate_response(client, prompts, webtext, person))

    output = combine_dicts(all_output)
    return output
