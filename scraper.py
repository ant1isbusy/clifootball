
import re # regex
import requests
import time

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
    print("Loading data ...")
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

def pandas_query(data, player):
    df = pd.DataFrame(data)

    # printAvailable seasons:
    print("")
    for i in range (len(player.teams)):
        print("(" + str((i + 1)) + ") " + player.teams[i][0] + "/" + str(int(player.teams[i][0]) + 1) + " - " + player.teams[i][1]) 

    season_selected = 0
    while True:
        temp = input("Select season to analyze: ")
        if temp.isdigit():
            season_selected = int(temp) - 1
            if 0 <= season_selected < len(player.teams):
                break
            else:
                print(f"Please enter a number between 1 and {len(player.teams)}.")
        else:
            print("Invalid input. Please enter a number.")
    
    season = player.teams[season_selected][0]

    season_df = df[df["season"] == season]
    print(season_df.columns)

    
    goals = season_df[season_df["result"] == "Goal"]
    print(goals)

def scrapePlayer(ID):
    json_data, player = getRawJsonPlayer(ID)
    print("Current team: " + red + player.curr_team + reset)
    pandas_query(json_data, player)

# TODO: https://www.footballfancast.com/premier-league-stadims-pitch-sizes-ranked-biggest-smallest/
    # take the different pitchsizes into consideration, not all pitches are of the same size in the EPL

    # in the top 5 leagues -> calculate pitch size, based on that, the calculations of X,Y shall happen, have a hashmap: league -> avg pitch dimensions.
    
    # take defenders into account, or players which do not have any goals or shots, then theirshotmap is empty
