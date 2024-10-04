
import re # regex
import requests

import json
import pandas as pd

from bs4 import BeautifulSoup as BS

green = "\033[92m"
red = "\033[91m"
reset = "\033[0m"

def getRawJsonPlayer(ID):
    response = requests.get("https://understat.com/player/" + ID)
    if response.status_code != 200:
        print("Client Error!")
    
    html = BS(response.content, "html.parser")

    title_tag = html.find('title')
    player_name = title_tag.text.split('|')[0].strip() # strip excess spaces around the name

    print("Player selected: " + red + player_name + reset)

    string_soup = str(html)

    shotsData = re.search("var shotsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)

    # removing escape characters:
    data = json.loads(shotsData.encode('utf8').decode('unicode_escape'))
    return data

def pandas_query(data):
    df = pd.DataFrame(data)

def scrapePlayer(ID):
    json_data = getRawJsonPlayer(ID)
    pandas_query(json_data)



