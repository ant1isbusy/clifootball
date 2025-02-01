import scraper as sc

import inquirer
import threading
import time
import itertools
import platform
import sys
import os
from datetime import datetime
import sqlite3 as sql


# ANSI codes
blue = "\033[94m"
yellow = "\033[93m"
green = "\033[92m"
red = "\033[91m"
ansi_reset = "\033[0m"
black = "\033[90m"
cyan = "\033[96m"
magenta = "\033[95m"
white = "\033[97m"
bright_gray = "\033[90m"
bright_red = "\033[91m"
bright_green = "\033[92m"
bright_yellow = "\033[93m"
bright_blue = "\033[94m"
bright_magenta = "\033[95m"
bright_cyan = "\033[96m"
bright_white = "\033[97m"

LEAGUES = ["EPL", "La_liga", "Bundesliga", "Serie_a"]

class CommandHandler:
    def __init__(self):
        self.league_id = None
        self.league_name = None
        self.loading = False
        self.player = (None, None)
        self.team = None

    def findPlayer(self):
        player_name = input("Enter player: ")
        player_name = player_name.strip().lower().title()

        # split the input to check for first and/or last name
        name_parts = player_name.split()

        matches = []

        conn = sql.connect('league.db')
        cursor = conn.cursor()

        if len(name_parts) == 1:
            cursor.execute("""
                SELECT p.player_id, p.name, p.team_title
                FROM Players p
                INNER JOIN Teams t ON p.team_id = t.id
                WHERE p.name LIKE ?
                AND t.league_id = ?
            """, (f"%{name_parts[0]}%", self.league_id,))

        elif len(name_parts) == 2:
            first_name, last_name = name_parts

            cursor.execute("""
                SELECT p.player_id, p.name, p.team_title
                FROM Players p
                INNER JOIN Teams t ON p.team_id = t.id
                WHERE p.name LIKE ?
                AND p.name LIKE ?
                AND t.league_id = ? 
            """, (f"%{first_name}%", f"%{last_name}%", self.league_id,))
        matches = cursor.fetchall()

        # print(matches)
        cursor.close()
        conn.close()

        return matches

    def loading_animation(self, message="Loading league data "):
        for frame in itertools.cycle([".", "..", "..."]):
            if not self.loading:
                break
            sys.stdout.write(f"\r{message}{frame}")
            sys.stdout.flush()
            time.sleep(0.5)
    
    def playerMenu(self):
        questions = [
            inquirer.List("option",
                        message="Choose an option",
                        choices=["(1) Create shotmap (png)",
                                 "(2) Export shot data (csv)",
                                 "(3) Show goals",
                                 "(4) Show scouting report",
                                 "(5) Go back",
                                 "(6) Quit"] ), ]

        answers = inquirer.prompt(questions)
        opt_selected = int(answers["option"][1])

        if opt_selected == 3:
            self.seasonGoals()
        elif opt_selected == 4:
            data = sc.FBREF_Scouting(self.player[1])
            printScoutingReport(data)
        elif opt_selected == 5:
            clearTerminal()
            return True
        elif opt_selected == 6:
            exit()
        return False
    
    def seasonGoals(self):
        # query the amount of goals per season:
        conn = sql.connect("player.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT season, team
            FROM player_teams
            WHERE player_id = ?
        """, (self.player[0],))
        pre_processing = cursor.fetchall()
        season_team_mapping = {}
        seasons = []

        for season, team in pre_processing:
            if season in season_team_mapping:
                season_team_mapping[season] += f"/{team}"
            else:
                season_team_mapping[season] = team

        seasons = [(season, teams) for season, teams in season_team_mapping.items()]

        season_goal_counts = []

        for season in seasons:
            year = season[0] 
            cursor.execute("""
                SELECT COUNT(*)
                FROM shots
                WHERE player_id = ?
                AND season = ?
                AND result = 'Goal'
            """, (self.player[0], year, ))
            goal_count = cursor.fetchone()[0]
            season_goal_counts.append((year, goal_count))

        printGoalsHistogram(season_goal_counts)

        season_goal_counts.sort(key=lambda x: x[0], reverse=True)
        s_opts = []
        for i in range (len(seasons)):
            s_opts.append("(" + str((i + 1)) + ") " + str(seasons[i][0]) + "/" + str(seasons[i][0] + 1)[-2:] + " - " + seasons[i][1]) 

        season_selected = 0

        inq_seasons = [
            inquirer.List("season",
                        message="Choose a season",
                        choices=s_opts, ), ]

        answers = inquirer.prompt(inq_seasons)
        idx = int(answers["season"][1])
        season_selected = seasons[idx - 1][0]
        team_playing_for = seasons[idx - 1][1]

        cursor.execute("""
                SELECT date, h_team, a_team, situation, minute
                FROM shots
                WHERE player_id = ?
                AND season = ?
                AND result = 'Goal'
            """, (self.player[0], season_selected))
        
        goals = cursor.fetchall()
        self.printGoals(goals, team_playing_for)

    def printGoals(self, goals, team_playing_for):
        if not goals:
            print("No goals scored in this season.")
            return
            
        datetime_format = "%Y-%m-%d %H:%M:%S"
        goals = [(datetime.strptime(g[0], datetime_format), *g[1:]) for g in goals]

        # Print the table header
        print(f"{' No.':<2} | {'Min':<4} | {'Against':<25} | {'Situation':<15} | {'Date':<10}")
        print("=" * 67)

        index = 1
        for _, row in enumerate(goals):
            # Determine the team the goal was scored against
            if row[1] == team_playing_for:
                team_against = row[2]
            else:
                team_against = row[1]
            
            # Extract minute, situation, and format the date
            minute = row[4]
            situation = row[3]
            date = row[0].strftime("%d.%m.%y")
            
            # Print the formatted goal information
            print(f" {index:>3} | {minute:<4} | {team_against:<25} | {situation:<15} | {date:<10}")
            index += 1
        
        print("")

    def printLeagueOptions(self, name, id):
        print("\nSelected: " + green + name + ansi_reset)
        questions = [
            inquirer.List("option",
                        message="Choose an option",
                        choices=["(1) Search player by name",
                                "(2) Show league table",
                                "(3) Select team",
                                "(4) Go back to league selection"], ), ]

        answers = inquirer.prompt(questions)
        opt_selected = int(answers["option"][1])
        
        # search player by name:
        if opt_selected == 1:
            clearTerminal()
            matches = self.findPlayer()
            if matches:
                player_selected = None
                if len(matches) == 1:
                    player_selected = matches[0]
                else:
                    player_names = [f"({i}) {match[1]:<20} - {match[2]:<10}" for i, match in enumerate(matches, start=1)]
                    questions = [
                    inquirer.List("player",
                                message="Choose an option",
                                choices=player_names,
                                ), ]

                    answers = inquirer.prompt(questions)
                    idx = int(answers["player"][1])

                    player_selected = matches[idx - 1]

                player_id, fullname, _ = player_selected
                print(f"Selected: " + yellow + fullname + ansi_reset)
                if self.player[0] != player_id:
                    sc.scrapePlayer(player_id)
                self.player = (player_id, fullname)
                while True:
                    if self.playerMenu():
                        break
            else:
                print("No match found, try again: ")

        # league table
        elif opt_selected == 2:
            clearTerminal()
            print(green + name + " League Table" + ansi_reset)
            printLeagueTable(id)

        # select team:
        elif opt_selected == 3:
            clearTerminal()
            print("TODO")
            return
            arr = [team.name for team in league.teams]    
            teams = [
            inquirer.List("team",
                        message="Choose a team:",
                        choices=arr,
                        ), ]
            
            answer = inquirer.prompt(teams)
            print("Selected: " + yellow + answer["team"] + ansi_reset)
        
        # go back to main menu
        else:  
            clearTerminal()
            return True

        return False
    
    def main_menu(self):
        while True:
            print("")

            questions = [
                inquirer.List("league",
                            message="Choose a league",
                            choices=["(1) Premier League",
                                     "(2) La Liga",
                                     "(3) Bundesliga", 
                                     "(4) Serie A", 
                                     "(5) quit"], ), ]

            answer = inquirer.prompt(questions)
            opt_selected = int(answer["league"][1])
            if opt_selected == 5:
                return

            league_link = LEAGUES[opt_selected - 1]

            if self.league_id is None or self.league_name != league_link:
                loading_THR = threading.Thread(target=self.loading_animation)
                self.loading = True
                loading_THR.start()
                
                id = sc.buildLeagueDB(league_link)
                self.loading = False
                loading_THR.join()

                self.league_id = id
                self.league_name = league_link

            name = answer["league"][4:]
            clearTerminal()
            while True:
                if self.printLeagueOptions(name, id):
                    break

def clearTerminal():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def printScoutingReport(scouting_data):
    print("Scouting report\n")

    for stat in scouting_data:
        line = f" {stat['Statistic']:<24} | {stat['Per 90']:<5} | "
        # create bar which we will add to the line, depending on the percentile,
        # we calculate the length of the bar
        bar = "█" * int(int(stat["Percentile"]) / 5)
        line += bar
        print(line)

    print("")


def printGoalsHistogram(season_goal_counts):
    
    season_goal_counts.sort(key=lambda x: x[0])
    last_seasons = season_goal_counts

    years = [str(year)[-2:] for year, _ in last_seasons]
    goals = [goals for _, goals in last_seasons]
    if all(goal == 0 for goal in goals):
        print("No goals scored yet.")
        return
    max_goals = max(goals, default=1)
    bar_height = 10

    # we take care of the case that only one goal is scored, we dont want an empty bar, it looks silly
    scaled_goals = [int(goal * bar_height / max_goals) if goal != 1 else 1 for goal in goals]
    line = "-" * 2 + "-" * (4 * len(years) - 1)
    len_x = len(line)
    print("Season".center(len_x))
    print(" " * 2 + "  ".join(years))
    print(line)

    for level in range(bar_height, 0, -1):
        row = []
        for bar in scaled_goals:
            row.append((blue + "██" + ansi_reset) if bar >= level else "  ")
        print("  " + "  ".join(row))

    print(" " * 2 + "  ".join(f"{goal:2}" for goal in goals))
    print(line)
    print("Goals".center(len_x))

def printLeagueTable(league_id):
    conn = sql.connect('league.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, matches_played, wins, draws, losses, 
               goals_scored, goals_conceded, points
        FROM Teams
        WHERE league_id = ?
        ORDER BY points DESC, (goals_scored - goals_conceded) DESC, goals_scored DESC
    """, (league_id,))

    teams = cursor.fetchall()

    # Print league table header
    print(f"{'Team':<25} | {'P':<4} | {'W':>4} | {'D':>4} | {'L':>4} | {'GD':>4} | {'Points':>5}")
    print("=" * 70)

    # Print each team in the league table
    for team in teams:
        team_name = team[0]
        matches = team[1]
        wins = team[2]
        draws = team[3]
        losses = team[4]
        goals_scored = team[5]
        goals_against = team[6]
        points = team[7]
        goal_difference = goals_scored - goals_against

        print(f"{team_name:<25} | {matches:<4} | {wins:>4} | {draws:>4} | {losses:>4} | {goal_difference:>4} | {points:>6}")

    conn.close()

if __name__ == "__main__":

    sc.getOrGenerateFBREFKey()
    command_handler = CommandHandler()
    command_handler.main_menu()
    print("Have a good day!")
    
    
