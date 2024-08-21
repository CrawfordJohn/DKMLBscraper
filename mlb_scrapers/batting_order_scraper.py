import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

# URL of the website to scrape
url = f'https://www.mlb.com/starting-lineups/{datetime.now().date().strftime("%Y-%m-%d")}'

# Send a GET request to the URL
response = requests.get(url)

# Check if the request was successful (status code 200)
if response.status_code == 200:
    # Parse the HTML content of the page
    soup = BeautifulSoup(response.content, 'html.parser')
    batting_lineups = pd.DataFrame()
    # Find all article titles on the page
    main_content = soup.find('main')
    lineup_boxes = main_content.find('section', class_='starting-lineups')
    games = lineup_boxes.find_all('div', class_='starting-lineups__matchup')

    team_names = []
    pitcher_names = []
    player_names = []
    batting_order = []
    for game in games:
        away_lineup = game.find('ol', class_='starting-lineups__team starting-lineups__team--away')
        away_names = away_lineup.find_all('a')
        for name in away_names:
            if name != 'TBD':
                player_names.append(name.text.strip())

        home_lineup = game.find('ol', class_='starting-lineups__team starting-lineups__team--home')
        home_names = home_lineup.find_all('a')
        for name in home_names:
            if name != 'TBD':
                player_names.append(name.text.strip())

        away_team = game.find('span', 'starting-lineups__team-name starting-lineups__team-name--away').text.strip()
        home_team = game.find('span', 'starting-lineups__team-name starting-lineups__team-name--home').text.strip()

        pitchers = game.find_all('div', class_='starting-lineups__pitcher-summary')
        away_pitcher = pitchers[0]
        home_pitcher = pitchers[-1]

        away_pitcher_name = away_pitcher.find('div', class_="starting-lineups__pitcher-name").text.strip()
        home_pitcher_name = home_pitcher.find('div', class_="starting-lineups__pitcher-name").text.strip()
        if len(away_names) == 9:
            pitcher_names.extend([home_pitcher_name]*9)
            batting_order.extend([i for i in range(1, 10)])
            team_names.extend([away_team]*9)
        if len(home_names) == 9:
            pitcher_names.extend([away_pitcher_name]*9)
            batting_order.extend([i for i in range(1, 10)])
            team_names.extend([home_team]*9)
    df = pd.DataFrame()
    df['name'] = player_names
    df['batting_order'] = batting_order
    df['team'] = team_names
    df['opp_pitcher'] = pitcher_names
    df.to_csv('mlb_scrapers/batting_lineup.csv', ignore_index=True)

else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")