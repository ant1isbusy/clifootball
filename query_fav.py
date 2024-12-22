
import sys
import scraper as sc

if __name__ == "__main__":
    favorite = None
    league = None
    if len(sys.argv) == 3:
        league = sys.argv[1]
        favorite = sys.argv[2]
    sc.printLeagueTable(league, favorite)