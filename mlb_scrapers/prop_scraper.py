import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def link_scraper():
    link = "https://sportsbook.draftkings.com"
    prop_extension = "?category=odds&subcategory=batter-props"
    response = requests.get(f"{link}/leagues/baseball/mlb")
    soup = BeautifulSoup(response.text, 'html.parser')
    tables = soup.find_all('tbody', class_="sportsbook-table__body")
    home = []
    away = []
    links = []
    i = 0
    for table in tables:
        table = table.find_all('tr')
        for tr in table:
            a_element = tr.find('a', class_="event-cell-link")
            team_name = a_element.find('div', class_ = "event-cell__name-text").text
            if i % 2 == 0:
                away.append(team_name)
                links.append(link + a_element.get('href') + prop_extension)
            else:
                home.append(team_name)
            i+=1

    data_dict = {"away":away, "home":home, "link":links}
    data = pd.DataFrame(data_dict)
    return data

def initialize_driver(link):
    driver = webdriver.Firefox()
    driver.get(link)
    page_source= driver.page_source
    driver.quit()
    return page_source

def check_avail(link):
    soup = BeautifulSoup(requests.get(link).text, "html.parser")
    if soup.find('div', class_="sportsbook-tabbed-subheader__tabs").find('a', id="subcategory_Batter Props") is None:
        return False
    return True
def scrape_props(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    table = soup.find('div', class_="sportsbook-responsive-card-container__card selected")
    odds_table = table.findChildren(recursive=False)[1]

    players = []
    over_lines = []
    over_odds = []
    under_lines = []
    under_odds = []
    bet_types = []
    for category in odds_table.children:
    #category = odds_table.findChildren(recursive=False)[0]
        stat_name = category.find('a', class_="sportsbook-event-accordion__title active").text
        if category.find('table', class_="sportsbook-table") is None:
            continue
        row = category.find('tbody', class_='sportsbook-table__body').find_all('tr')
        for player in row:
            bet_types.append(stat_name)
            players.append(player.find('span', class_="sportsbook-row-name").text)
            lines = player.find_all('span', class_="sportsbook-outcome-cell__line")
            if len(lines) > 0:
                over_lines.append(lines[0].text)
                under_lines.append(lines[1].text)
            else:
                over_lines.append(None)
                under_lines.append(None)
            odds = player.find_all('span', class_="sportsbook-odds american default-color")
            over_odds.append(odds[0].text)
            if len(odds) > 1:
                under_odds.append(odds[1].text)
            else:
                under_odds.append(None)
        df = pd.DataFrame()
        df['players'] = players
        df['over_lines'] = over_lines
        df['over_odds'] = over_odds
        df['under_lines'] = under_lines
        df['under_odds'] = under_odds
        df['bet_type'] = bet_types

    return df

def calculate_hold(df):
    hold_list = []
    for i, row in df.iterrows():
        if (row['over_odds'] is not None) & (row['under_odds'] is not None):
            if row['over_odds'].str[0] == '+':
                over_prob = 100 / (100 +int(row['over_odds'].str[1:]) )
                under_prob = int(row['under_odds'].str[1:]) / (100 + int(row['under_odds'].str[1:]))
            else:
                over_prob = int(row['over_odds'].str[1:]) / (100 + int(row['over_odds'].str[1:]))
                under_prob = 100 / (100 +int(row['under_odds'].str[1:]))
            hold = over_prob + under_prob - 1
        hold_list.append(hold)
    df['hold'] = hold_list
    return df

if __name__ == "__main__":
    all_data = []
    link_df = link_scraper()
    for _, row in link_df.iterrows():
        if check_avail(row['link']):
            page_source = initialize_driver(row['link'])
            game_df = scrape_props(page_source)
            game_df['home_tm'] = row['home']
            game_df['away_tm'] = row['away']
            all_data.append(game_df)
    if len(all_data) > 1:
        master_df = pd.concat(all_data, ignore_index=True)
        master_df.to_csv('6pm_572024.csv')