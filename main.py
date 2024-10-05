import scraper as sc

import inquirer

# ANSI codes
blue = "\033[94m"
yellow = "\033[93m"
green = "\033[92m"
red = "\033[91m"
ansi_reset = "\033[0m"

LEAGUES = [ ("premier league", "EPL"),
            ("epl", "EPL"),
            ("laliga", "La_liga"),
            ("la liga", "La_liga"),
            ("serie a", "Serie_A"),
            ("bundesliga", "Bundesliga")]

def getLeague():
    print(blue + "Which league do you want to analyse?" + ansi_reset)

    while(True):

        league_string = input("League: ")

        league_string = league_string.lower()

        for league in LEAGUES:
            if league_string == league[0]:
                return league[1]
            
        print("No such league found, try again (top 5 leagues only)! ")

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

        print(f"{team_name:<25} | {matches:<4} | {wins:>4} | {draws:>4} | {loses:>4} | {goal_difference:>4} | {red}{points:>5}{ansi_reset}")

def printLeagueOptions(league : sc.League):
    print("")

    print("Selected: " + green + (league.name.upper()) + ansi_reset)
    questions = [
        inquirer.List("option",
                    message="Choose an option:",
                    choices=["(1) Search player by name", "(2) Show league table ", "(3) Select team"],
                    ),
    ]

    answers = inquirer.prompt(questions)
    opt_selected = int(answers["option"][1])
    
    # search player by name:
    if opt_selected == 1:
        pass
    # league table
    elif opt_selected == 2:
        print(green + league.name.upper() + " League Table" + ansi_reset)
        printLeagueTable(league)

    # select team:
    else:
        arr = [team.name for team in league.teams]    
        teams = [
        inquirer.List("team",
                    message="Choose a team:",
                    choices=arr,
                    ), ]
        
        answer = inquirer.prompt(teams)
        print("Selected: " + yellow + answer["team"] + ansi_reset)

def getPlayerID() -> int:
    print("Please enter the ID of the player you want to analyse!")

    ID = input("ID: ")
    return ID;

if __name__ == "__main__":
    lig_str = getLeague()
    league_obj = sc.buildLeague(lig_str)
    printLeagueOptions(league_obj)
    
    
