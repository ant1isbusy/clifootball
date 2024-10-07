import scraper as sc
import pandas as pd

import inquirer
import threading
import time
import itertools
import platform
import sys
import os

# ANSI codes
blue = "\033[94m"
yellow = "\033[93m"
green = "\033[92m"
red = "\033[91m"
ansi_reset = "\033[0m"

LEAGUES = ["EPL", "La_liga", "Bundesliga", "Serie_a"]

class CommandHandler:
    def __init__(self):
        self.league = None
        self.loading = False
        self.Player = None

    def findPlayer(self):
        player_name = input("Enter player: ")
        player_name = player_name.strip().lower().title()

        # split the input to check for first and/or last name
        name_parts = player_name.split()

        matches = []

        print(name_parts, len(name_parts))

        for player in self.league.players:
            full_name = player.name

            if len(name_parts) == 1:
                if name_parts[0] in full_name.split():
                    matches.append(player)
            elif len(name_parts) == 2:
                # If both first and last names are provided
                first_name, last_name = name_parts
                print(full_name)
                
                # Split the full name and handle cases where a player might not have a last name
                name_parts_in_full = full_name.split(maxsplit=1)

                if len(name_parts_in_full) == 2:
                    player_first, player_last = name_parts_in_full

                    # Match both first and last names
                    if first_name == player_first and last_name == player_last:
                        matches.append(player)
                elif len(name_parts_in_full) == 1:
                    # Only one name exists, check if it matches the input first name
                    if first_name == name_parts_in_full[0] or last_name == name_parts_in_full[0]:
                        matches.append(player)

        return matches

    def loading_animation(self, message="Loading league data"):
        for frame in itertools.cycle([".", "..", "..."]):
            if not self.loading:
                break
            sys.stdout.write(f"\r{message}{frame}")
            sys.stdout.flush()
            time.sleep(0.5)
    
    def playerMenu(self, player : sc.Player):
        df, self.Player = sc.scrapePlayer(player.id) # shall return a dataframe
        questions = [
            inquirer.List("option",
                        message="Choose an option",
                        choices=["(1) Create shotmap (png)",
                                 "(2) Export shot data (csv)",
                                 "(3) Show Goals",
                                 "(4) Go back"], ), ]

        answers = inquirer.prompt(questions)
        opt_selected = int(answers["option"][1])

        if opt_selected == 3:
            self.seasonQuery(df ,self.Player)

        if opt_selected == 4:
            clearTerminal()
            return True
        
        return False
    
    def seasonQuery(self, df, player):

        # printAvailable seasons:
        s_opts = []
        for i in range (len(player.teams_played_for)):
            s_opts.append("(" + str((i + 1)) + ") " + player.teams_played_for[i][0] + "/" + str(int(player.teams_played_for[i][0]) + 1) + " - " + player.teams_played_for[i][1]) 

        season_selected = 0

        seasons = [
            inquirer.List("season",
                        message="Choose an option",
                        choices=s_opts, ), ]

        answers = inquirer.prompt(seasons)
        idx = int(answers["season"][1])
        season_selected = player.teams_played_for[idx - 1][0]
        team_playing_for = player.teams_played_for[idx - 1][1]

        print(season_selected)

        season_df = df[df["season"] == season_selected]
        
        goals = season_df[season_df["result"] == "Goal"]
        goals = goals[["player","minute", "player_assisted", "h_team", "a_team", "date", "situation", "shotType"]]
        self.printGoals(goals, team_playing_for)

    def printGoals(self, goals_df, team_playing_for):

        if goals_df.empty:
            print("No goals scored in this season.")
            return
            
        goals_df["date"] = pd.to_datetime(goals_df["date"], errors="coerce")

        # Print the table header
        print(f"{'No.':<2} | {'Min':<4} | {'Against':<25} | {'Situation':<15} | {'Date':<10}")
        print("=" * 60)

        index = 1
        for _, row in goals_df.iterrows():
            # Determine the team the goal was scored against
            if row["h_team"] == team_playing_for:
                team_against = row["a_team"]
            else:
                team_against = row["h_team"]
            
            # Extract minute, situation, and format the date
            minute = row["minute"]
            situation = row["situation"]
            date = row["date"].strftime("%d.%m.%y")
            
            # Print the formatted goal information
            print(f"{index:<3} | {minute:<4} | {team_against:<25} | {situation:<15} | {date:<10}")
            index += 1

    def printLeagueOptions(self, name):
        league = self.league
        print("\nSelected: " + green + league.name.upper() + ansi_reset)
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
                    player_names = [f"({i}) {match.name}" for i, match in enumerate(matches, start=1)]
                    questions = [
                    inquirer.List("player",
                                message="Choose an option",
                                choices=player_names,
                                ), ]

                    answers = inquirer.prompt(questions)
                    idx = int(answers["player"][1])

                    player_selected = matches[idx - 1]
                    
                print(player_selected.name)

                while True:
                    if self.playerMenu(player_selected):
                        break

            else:
                print("No match found, try again: ")

        # league table
        elif opt_selected == 2:
            clearTerminal()
            print(green + league.name.upper() + " League Table" + ansi_reset)
            printLeagueTable(league)

        # select team:
        elif opt_selected == 3:
            clearTerminal()
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
            print("we pressed back!")
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
                                     "(5) quit"], ),
            ]

            answer = inquirer.prompt(questions)
            opt_selected = int(answer["league"][1])
            if opt_selected == 5:
                return

            league_link = LEAGUES[opt_selected - 1]

            if self.league == None or self.league.name != league_link:

                loading_THR = threading.Thread(target=self.loading_animation)
                self.loading = True
                loading_THR.start()
                
                self.league = sc.buildLeague(league_link)
                self.loading = False

                loading_THR.join()

            name = answer["league"][4:]
            clearTerminal()
            while True:
                if self.printLeagueOptions(name):
                    break
                print("going into next iter")

def clearTerminal():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")

def printLeagueTable(league: sc.League):
    print(f"{'Team':<25} | {'P':<4} | {'W':>4} | {'D':>4} | {'L':>4} | {'GD':>4} | {'Points':>5}")
    print("=" * 70)

    for team in league.teams:
        team_name = team.name
        goals_scored = team.goals_scored
        goals_against = team.goals_against
        goal_difference = goals_scored - goals_against
        points = team.pts
        matches = team.matches_p
        wins = team.w
        loses = team.l
        draws = team.d

        print(f"{team_name:<25} | {matches:<4} | {wins:>4} | {draws:>4} | {loses:>4} | {goal_difference:>4} | {red}{points:>6}{ansi_reset}")


if __name__ == "__main__":

    command_handler = CommandHandler()
    command_handler.main_menu()
    print("Have a good day!")
    
    
