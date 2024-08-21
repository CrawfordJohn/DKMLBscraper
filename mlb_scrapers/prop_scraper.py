import requests
from datetime import datetime, date
import time
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from devig import true_odds

# Async function to get page content
async def fetch(session, url):
    async with session.get(url) as response:
        return await response.text()

# Function to initialize Selenium WebDriver
def initialize_driver(link):
    options = Options()
    options.add_argument("--headless")  # Run headless for speed
    driver = webdriver.Chrome(options=options)
    driver.get(link)
    page_source = driver.page_source
    driver.quit()
    return page_source

# Async wrapper for Selenium WebDriver
async def fetch_page_source(link):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, initialize_driver, link)

# Function to scrape links from the main page
async def link_scraper():
    link = "https://sportsbook.draftkings.com"
    prop_extension = "?category=odds&subcategory=batter-props"
    
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, f"{link}/leagues/baseball/mlb")
        soup = BeautifulSoup(response, 'html.parser')
    
    tables = soup.find_all('tbody', class_="sportsbook-table__body")
    home = []
    away = []
    links = []
    i = 0
    for table in tables:
        table = table.find_all('tr')
        for tr in table:
            a_element = tr.find('a', class_="event-cell-link")
            team_name = a_element.find('div', class_="event-cell__name-text").text
            if i % 2 == 0:
                away.append(team_name)
                links.append(link + a_element.get('href') + prop_extension)
            else:
                home.append(team_name)
            i += 1

    data_dict = {"away": away, "home": home, "link": links}
    data = pd.DataFrame(data_dict)
    return data

# Function to check availability
async def check_avail(session, link):
    response = await fetch(session, link)
    soup = BeautifulSoup(response, "html.parser")
    if soup.find('div', class_="sportsbook-tabbed-subheader__tabs").find('a', id="subcategory_Batter Props") is None:
        return False
    return True

# Function to scrape props
def scrape_props(page_source):
    soup = BeautifulSoup(page_source, 'html.parser')
    table = soup.find('div', class_="sportsbook-responsive-card-container__card selected")
    players = []
    over_lines = []
    over_odds = []
    under_lines = []
    under_odds = []
    bet_types = []
    if table:
        odds_table = table.findChildren(recursive=False)[1]

        for category in odds_table.children:
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
    
    df = pd.DataFrame({
        'players': players,
        'over_lines': over_lines,
        'over_odds': over_odds,
        'under_lines': under_lines,
        'under_odds': under_odds,
        'bet_type': bet_types
    })

    return df

# Function to calculate hold
def calculate_hold(df):
    hold_list = []
    for i, row in df.iterrows():
        if (row['over_odds'] is not None) & (row['under_odds'] is not None):
            if row['over_odds'].startswith('+'):
                over_prob = 100 / (100 + int(row['over_odds'][1:]))
                under_prob = int(row['under_odds'][1:]) / (100 + int(row['under_odds'][1:]))
            else:
                over_prob = int(row['over_odds'][1:]) / (100 + int(row['over_odds'][1:]))
                under_prob = 100 / (100 + int(row['under_odds'][1:]))
            hold = over_prob + under_prob - 1
            hold_list.append(hold)
        else:
            hold_list.append(None)
    df['hold'] = hold_list
    return df

async def main():
    file = open('scheduler_log.txt', 'a')
    file.write(f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} - Process Started\n')
    all_data = []
    link_df = await link_scraper()
    async with aiohttp.ClientSession() as session:
        tasks = []
        for _, row in link_df.iterrows():
            task = asyncio.create_task(check_avail(session, row['link']))
            tasks.append(task)
        availabilities = await asyncio.gather(*tasks)
    file.write(f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} - Links Pulled\n')
    for available, row in zip(availabilities, link_df.iterrows()):
        if available:
            print(row[1]['link'])
            page_source = await fetch_page_source(row[1]['link'])
            game_df = scrape_props(page_source)
            game_df['home_tm'] = row[1]['home']
            game_df['away_tm'] = row[1]['away']
            all_data.append(game_df)
    
    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        master_df['date'] = date.today().strftime("%Y-%m-%d")
        true_odds(master_df).to_csv(f'C:\\Users\\jcraw\\Documents\\GitHubRepos\\DKMLBscraper\\mlb_scrapers\\data\\{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv', index=False)
    file.write(f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} - Props Successfully Scraped\n')
if __name__ == "__main__":
    asyncio.run(main())