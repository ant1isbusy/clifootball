
import re # regex
import requests
import time
from datetime import datetime

import platform
import json
import os
import pandas as pd
import sqlite3 as sql

from bs4 import BeautifulSoup as BS

TESTING = True

class Player:
    def __init__(self, id, name, teams, curr):
        self.id = id
        self.name = name
        self.teams_played_for = teams
        self.curr_team = curr

def initLeagueDB(cursor):
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
        team_title TEXT,
        team_id INTEGER,
        FOREIGN KEY (team_id) REFERENCES Teams (id)
    ) """)
    
def initPlayerTables(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS player_teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        season INTEGER,
        team TEXT,
        FOREIGN KEY(player_id) REFERENCES players(id));
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shot_id TEXT,
        minute INTEGER,
        result TEXT,
        X REAL,
        Y REAL,
        xG REAL,
        player_id INTEGER,
        situation TEXT,
        shotType TEXT,
        match_id INTEGER,
        h_team TEXT,
        a_team TEXT,
        h_goals INTEGER,
        a_goals INTEGER,
        date TEXT,
        season INTEGER,
        player_assisted TEXT,
        lastAction TEXT,
        FOREIGN KEY(player_id) REFERENCES players(id));
    """)
    
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

def printLeagueTable(league_str, favorite=None):
    """A function for fast output to the terminal, 
    when you want to check the current table without further operations"""
    print("Fetching data ...\n")
    teams_data, player_data = getLeagueData(league_str)

    teams = []
    for team in teams_data.values():
        name = team["title"]
        history_df = pd.DataFrame(team["history"])
        m_played = len(history_df)
        pts = history_df["pts"].sum()
        g_scored = history_df["scored"].sum()
        g_against = history_df["missed"].sum()
        wins = history_df["wins"].sum()
        draws = history_df["draws"].sum()
        losses = history_df["loses"].sum()

        teams.append({
            "name": name,
            "matches_played": m_played,
            "points": pts,
            "goals_scored": g_scored,
            "goals_conceded": g_against,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "goal_difference": g_scored - g_against
        })

    sorted_teams = sorted(
        teams, 
        key=lambda t: (t["points"], t["goal_difference"], t["goals_scored"]), 
        reverse=True
    )

    print(f" {' ':>2} | {'Team':<25} | {'P':>2} | {'W':>2} | {'D':>2} | {'L':>2} | {'GD':>4} | {'Pts':>3}")
    print("=" * 66)

    for i, team in enumerate(sorted_teams):
        team_name = team["name"]
        matches = team["matches_played"]
        wins = team["wins"]
        draws = team["draws"]
        losses = team["losses"]
        points = team["points"]
        goal_difference = team["goal_difference"]

        if team_name == favorite:
            print(f"\033[91m {i+1:>2} | {team_name:<25} | {matches:>2} | {wins:>2} | {draws:>2} | {losses:>2} | {goal_difference:>4} | {points:>3}\033[0m")
            continue

        print(f" {i+1:>2} | {team_name:<25} | {matches:>2} | {wins:>2} | {draws:>2} | {losses:>2} | {goal_difference:>4} | {points:>3}")

def buildLeagueDB(league_str):
    """ Creates the league in SQL and returns the ID """

    if (os.path.exists("league.db")): 
        conn = sql.connect("league.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM Leagues where name = ?", (league_str, ))
        res = cursor.fetchone()
        if res and TESTING:
            return res[0]

    today = datetime.today()
    season_year = today.year
    # in august the new league season begins, need some time to get all the new players
    # into the database, so a rough estimate of the league season
    if (today.month <= 8):
        season_year = season_year - 1

    teams_data, player_data = getLeagueData(league_str)
    # init tables if they dont yet exist:
    conn = sql.connect("league.db")
    cursor = conn.cursor()

    initLeagueDB(cursor)
    
    cursor.execute(
        "INSERT INTO Leagues (name, season_year) VALUES (?, ?)",
        (league_str, season_year)
    )
    league_id_SQL = cursor.lastrowid

    team_data = []
    for team in teams_data.values():

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
    """
    INSERT INTO Teams (name, league_id, matches_played, points, goals_scored, goals_conceded, wins, draws, losses)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(name) DO UPDATE SET
        league_id = excluded.league_id,
        matches_played = excluded.matches_played,
        points = excluded.points,
        goals_scored = excluded.goals_scored,
        goals_conceded = excluded.goals_conceded,
        wins = excluded.wins,
        draws = excluded.draws,
        losses = excluded.losses
    """, 
    team_data )

    # get sql IDs of all teams:
    cursor.execute("SELECT id, name, wins FROM Teams WHERE league_id = ?", (league_id_SQL, ))
    teams_name_to_id = {row[1]: row[0] for row in cursor.fetchall()}

    all_players = []
    for player in player_data:
        team_title = player["team_title"]
        if "," in team_title:
            team_title = team_title.split(",")[-1]
        # store only the current team
        team_id = teams_name_to_id[team_title]
        if team_id:
            all_players.append((player["id"], player["player_name"], team_id, team_title))

    # insert all players into the DB:
    cursor.executemany("""INSERT INTO Players (player_id, name, team_id, team_title) VALUES (?, ?, ?, ?)
                       ON CONFLICT(player_id) DO UPDATE SET 
                       team_id = excluded.team_id,
                       team_title = excluded.team_title
                       """, all_players)
    conn.commit()
    conn.close()

    return league_id_SQL

def scrapePlayer(ID):
    response = requests.get("https://understat.com/player/" + str(ID))

    if response.status_code != 200:
        print("Client Error!")
        exit(0)
    
    raw_html = BS(response.content, "html.parser")
    string_soup = str(raw_html)

    season_json = re.search("var groupsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)
    season_data = json.loads(season_json.encode("utf8").decode("unicode_escape"))

    raw_shotdata = re.search("var shotsData .*= JSON.parse\('(.*)'\)", string_soup).group(1)
    shots_data = json.loads(raw_shotdata.encode("utf8").decode("unicode_escape"))

    if os.path.exists("player.db"):
        os.remove("player.db")

    conn = sql.connect("player.db")
    cursor = conn.cursor()

    initPlayerTables(cursor)

    curr_team = ""
    for entry in season_data["season"]:
        season = entry["season"]
        team = entry["team"]
        if curr_team == "":
            curr_team = team

        cursor.execute("""
            INSERT INTO player_teams (player_id, season, team)
            VALUES (?, ?, ?)
        """, (ID, season, team))
    
    shots_to_insert = []
    for shot in shots_data:
        shots_to_insert.append((
            shot['id'], shot['minute'], shot['result'], shot['X'], shot['Y'], shot['xG'],
            ID, shot['situation'], shot['shotType'], shot['match_id'], shot['h_team'],
            shot['a_team'], shot['h_goals'], shot['a_goals'], shot['date'], shot['season'], shot['player_assisted'],
            shot['lastAction']
        ))

    # Insert all shots data at once
    cursor.executemany("""
        INSERT INTO shots (
            shot_id, minute, result, X, Y, xG, player_id, situation, shotType,
            match_id, h_team, a_team, h_goals, a_goals, date, season, player_assisted, lastAction
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, shots_to_insert)

    conn.commit()
    conn.close()
    

# TODO: https://www.footballfancast.com/premier-league-stadims-pitch-sizes-ranked-biggest-smallest/
    # take the different pitchsizes into consideration, not all pitches are of the same size in the EPL

    # in the top 5 leagues -> calculate pitch size, based on that, the calculations of X,Y shall happen, have a hashmap: league -> avg pitch dimensions.
    
    # take defenders into account, or players which do not have any goals or shots, then theirshotmap is empty

    # options after entering league name: -> search player, show league table, etc.
