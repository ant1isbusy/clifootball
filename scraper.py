
import re # regex
import requests
import time
from datetime import datetime

import json
import pandas as pd

from bs4 import BeautifulSoup as BS

class Team:
    # TODO: games played!
    def __init__(self, name, history, pts, goals_scored, goals_against, matches_played, w, d, l):
        self.name = name
        self.history = history
        self.pts = pts
        self.w = w
        self.d = d
        self.l = l
        self.goals_scored = goals_scored
        self.goals_against = goals_against
        self.matches_p = matches_played

    def goal_difference(self):
        return self.goals_scored - self.goals_against

class League:
    def __init__(self, name, players, teams):
        self.name = name
        self.players = players
        self.teams = teams

class Player:
    def __init__(self, id, name, teams, curr):
        self.id = id
        self.name = name
        self.teams_played_for = teams
        self.curr_team = curr

def buildLeague(league_str):

    today = datetime.today()
    season_year = today.year
    # in august the new league season begins, need some time to get all the new players
    # into the database, so a rough estimate of the league season
    if (today.month <= 8):
        season_year = season_year - 1

    # get league data:
    response = requests.get("https://understat.com/league/" + league_str + "/" + str(season_year))
    if response.status_code != 200:
        print("Client Error!")
        exit(0)

    raw_html = BS(response.content, "html.parser")
    string_soup = str(raw_html).encode('utf-8').decode('unicode_escape')

    players_json = re.search(r"var playersData\s*=\s*JSON\.parse\('(.*)'\);", string_soup).group(1)
    players_json = players_json.replace("\\'", "'")
    player_data = json.loads(players_json)

    teams_json = re.search("var teamsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)
    teams_data = json.loads(teams_json.encode('utf8').decode('unicode_escape'))

    p_df = pd.DataFrame(player_data)
    player_database = p_df[["id", "player_name", "team_title"]]

    # teams on understat is a silly key - value map, we need to calculate points on our own
    teams_obj_list = []
    for team in teams_data.values():

        name = team["title"]
        history_df = pd.DataFrame(team["history"])
        m_played = len(history_df)
        pts = history_df["pts"].sum()
        g_scored = history_df["scored"].sum()
        g_against = history_df["missed"].sum()
        wins = history_df["wins"].sum()
        draws = history_df["draws"].sum()
        loses = history_df["loses"].sum()

        curr_team = Team(name, history_df, pts, g_scored, g_against, m_played, wins, draws, loses)
        teams_obj_list.append(curr_team)

    sorted_teams = sorted(teams_obj_list, key=lambda team: (team.pts, team.goal_difference(), team.goals_scored), reverse=True)   

    league_obj = League(league_str, player_database, sorted_teams)
    
    return league_obj

def getRawJsonPlayer(ID):
    print("Loading data ...")
    response = requests.get("https://understat.com/player/" + str(ID))

    if response.status_code != 200:
        print("Client Error!")
        exit(0)
    
    raw_html = BS(response.content, "html.parser")

    title_tag = raw_html.find('title')
    player_name = title_tag.text.split('|')[0].strip() # strip excess spaces around the name

    print("Player selected: " + player_name)

    string_soup = str(raw_html)

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
    return pd.DataFrame(data), selected_player

def pandas_query(df, player):

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
    data, player = getRawJsonPlayer(ID)
    print("Current team: " + player.curr_team)
    pandas_query(data, player)

# TODO: https://www.footballfancast.com/premier-league-stadims-pitch-sizes-ranked-biggest-smallest/
    # take the different pitchsizes into consideration, not all pitches are of the same size in the EPL

    # in the top 5 leagues -> calculate pitch size, based on that, the calculations of X,Y shall happen, have a hashmap: league -> avg pitch dimensions.
    
    # take defenders into account, or players which do not have any goals or shots, then theirshotmap is empty

    # options after entering league name: -> search player, show league table, etc.
