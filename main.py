
import scraper as sc

def getPlayerID() -> int:
    print("Please enter the ID of the player you want to analyse!")

    ID = input("ID: ")
    return ID;

if __name__ == "__main__":
    ID = getPlayerID()
    shot_data = sc.scrapePlayer(ID)
    
