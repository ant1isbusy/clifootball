
import re # regex
import requests

import json
import pandas as pd

from bs4 import BeautifulSoup as BS

green = "\033[92m"
red = "\033[91m"
reset = "\033[0m"

class Player:
    def __init__(self, name, teams, curr):
        self.name = name
        self.teams = teams
        self.curr_team = curr

def getRawJsonPlayer(ID):
    response = requests.get("https://understat.com/player/" + ID)
    if response.status_code != 200:
        print("Client Error!")

    
    html = BS(response.content, "html.parser")

    title_tag = html.find('title')
    player_name = title_tag.text.split('|')[0].strip() # strip excess spaces around the name

    print("Player selected: " + red + player_name + reset)

    string_soup = str(html)

    season_json = re.search("var groupsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)
    season_data = json.loads(season_json.encode('utf8').decode('unicode_escape'))

    season_team_list = []
    curr_team = ""
    for entry in season_data['season']:
        season = entry['season']
        team = entry['team']
        if not season_team_list:
            curr_team = team
        season_team_list.append((season, team))

    selected_player = Player(player_name, season_team_list, curr_team)    

    shotsData = re.search("var shotsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)

    # removing escape characters:
    data = json.loads(shotsData.encode('utf8').decode('unicode_escape'))
    return data, selected_player

def pandas_query(data):
    df = pd.DataFrame(data)
    season_selected = 0
    print(df.iloc[0])

def scrapePlayer(ID):
    json_data, player = getRawJsonPlayer(ID)
    print(player.curr_team)
    pandas_query(json_data)

# TODO: https://www.footballfancast.com/premier-league-stadims-pitch-sizes-ranked-biggest-smallest/
    # take the different pitchsizes into consideration, not all pitches are of the same size in the EPL

    # in the top 5 leagues -> calculate pitch size, based on that, the calculations of X,Y shall happen, have a hashmap: league -> avg pitch dimensions.
    

