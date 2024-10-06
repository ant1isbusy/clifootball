import scraper as sc

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

    def loading_animation(self, message="Loading league data"):
        for frame in itertools.cycle([".", "..", "..."]):
            if not self.loading:
                break
            sys.stdout.write(f"\r{message}{frame}")
            sys.stdout.flush()
            time.sleep(0.5)
    
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
                if printLeagueOptions(self.league, name):
                    break


def clearTerminal():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

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

def printLeagueOptions(league : sc.League, name):

    print("\nSelected: " + green + name.upper() + ansi_reset)
    questions = [
        inquirer.List("option",
                    message="Choose an option",
                    choices=["(1) Search player by name",
                             "(2) Show league table",
                             "(3) Select team",
                             "(4) Go back to league selection"],
                    ), ]

    answers = inquirer.prompt(questions)
    opt_selected = int(answers["option"][1])
    
    # search player by name:
    if opt_selected == 1:
        pass

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
        return True

    return False

if __name__ == "__main__":

    command_handler = CommandHandler()
    command_handler.main_menu()
    print("Have a good day!")
    
    
