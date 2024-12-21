
import re # regex
import requests
import time
from datetime import datetime

import json
import os
import pandas as pd
import sqlite3 as sql

from bs4 import BeautifulSoup as BS

def init_tables(cursor):
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Leagues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            season_year INTEGER
        ) """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            league_id INTEGER,
            matches_played INTEGER,
            points INTEGER,
            goals_scored INTEGER,
            goals_conceded INTEGER,
            wins INTEGER,
            draws INTEGER,
            losses INTEGER,
            FOREIGN KEY (league_id) REFERENCES Leagues (id)
        ) """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER UNIQUE,
            name TEXT,
            team_id INTEGER,
            FOREIGN KEY (team_id) REFERENCES Teams (id)
        ) """)
    
def getLeagueData(league_str):
    today = datetime.today()
    season_year = today.year
    # in august the new league season begins, need some time to get all the new players
    # into the database, so a rough estimate of the league season
    if (today.month <= 8):
        season_year = season_year - 1

    response = requests.get("https://understat.com/league/" + league_str + "/" + str(season_year))
    if response.status_code != 200:
        print("Client Error!")
        exit(0)

    raw_html = BS(response.content, "html.parser")
    string_soup = str(raw_html).encode("utf-8").decode("unicode_escape")

    players_json = re.search(r"var playersData\s*=\s*JSON\.parse\('(.*)'\);", string_soup).group(1)
    players_json = players_json.replace("\\'", "'")
    player_data = json.loads(players_json)

    teams_json = re.search("var teamsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)
    teams_data = json.loads(teams_json.encode('utf8').decode('unicode_escape'))

    return teams_data, player_data


def buildLeague(league_str):
    """ Creates the league in SQL and returns the ID """

    db_path = "football.db"
    if os.path.exists(db_path):
        os.remove(db_path)

    today = datetime.today()
    season_year = today.year
    # in august the new league season begins, need some time to get all the new players
    # into the database, so a rough estimate of the league season
    if (today.month <= 8):
        season_year = season_year - 1

    teams_data, player_data = getLeagueData(league_str, )
    
    # init tables if they dont yet exist:
    conn = sql.connect("football.db")
    cursor = conn.cursor()

    init_tables(cursor)
    
    cursor.execute(
        "INSERT INTO Leagues (name, season_year) VALUES (?, ?)",
        (league_str, season_year)
    )
    league_id_SQL = cursor.lastrowid

    team_data = []
    for i, team in enumerate(teams_data.values()):

        name = team["title"]
        history_df = pd.DataFrame(team["history"])
        m_played = len(history_df)
        pts = history_df["pts"].sum()
        g_scored = history_df["scored"].sum()
        g_against = history_df["missed"].sum()
        wins = history_df["wins"].sum()
        draws = history_df["draws"].sum()
        losses = history_df["loses"].sum()

        team_data.append((name, league_id_SQL, m_played, int(pts), int(g_scored), int(g_against), int(wins), int(draws), int(losses)))

    cursor.executemany(
        """INSERT INTO Teams (name, league_id, matches_played, points, goals_scored, goals_conceded, wins, draws, losses) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", team_data )

    # get sql IDs of all teams:
    cursor.execute("SELECT id, name, wins FROM Teams WHERE league_id = ?", (league_id_SQL,))
    teams_name_to_id = {row[1]: row[0] for row in cursor.fetchall()}


    all_players = []
    for player in player_data:
        team_title = player["team_title"]
        if "," in team_title:
            team_title = team_title.split(",")[-1]
        # store only the current team
        team_id = teams_name_to_id[team_title]
        if team_id:
            all_players.append((player["id"], player["player_name"], team_id))

    # insert all players into the DB:
    cursor.executemany("INSERT INTO Players (player_id, name, team_id) VALUES (?, ?, ?)", all_players)
    conn.commit()
    conn.close()

    return league_id_SQL


def getRawJsonPlayer(ID):
    response = requests.get("https://understat.com/player/" + str(ID))

    if response.status_code != 200:
        print("Client Error!")
        exit(0)
    
    raw_html = BS(response.content, "html.parser")

    title_tag = raw_html.find("title")
    player_name = title_tag.text.split("|")[0].strip() # strip excess spaces around the name

    string_soup = str(raw_html)

    season_json = re.search("var groupsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)
    season_data = json.loads(season_json.encode("utf8").decode("unicode_escape"))

    season_team_list = []
    curr_team = ""
    for entry in season_data["season"]:
        season = entry["season"]
        team = entry["team"]
        if not season_team_list:
            curr_team = team
        season_team_list.append((season, team))

    selected_player = Player(ID, player_name, season_team_list, curr_team)    

    shotsData = re.search("var shotsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)

    # removing escape characters:
    data = json.loads(shotsData.encode("utf8").decode("unicode_escape"))
    return pd.DataFrame(data), selected_player

def scrapePlayer(ID): 
    return getRawJsonPlayer(ID)

# TODO: https://www.footballfancast.com/premier-league-stadims-pitch-sizes-ranked-biggest-smallest/
    # take the different pitchsizes into consideration, not all pitches are of the same size in the EPL

    # in the top 5 leagues -> calculate pitch size, based on that, the calculations of X,Y shall happen, have a hashmap: league -> avg pitch dimensions.
    
    # take defenders into account, or players which do not have any goals or shots, then theirshotmap is empty

    # options after entering league name: -> search player, show league table, etc.
