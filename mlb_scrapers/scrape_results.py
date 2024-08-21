from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO


def scrape_results(date):
    # Step 1: Fetch the webpage
    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()))

    url = f'https://www.fangraphs.com/leaders/major-league?pos=all&stats=bat&lg=all&qual=y&type=0&season=2024&month=1000&season1=2024&ind=0&startdate={date}&enddate={date}&team=0&pagenum=1&pageitems=2000000000'
    driver.get(url)

    wait = WebDriverWait(driver, 10)  # Wait up to 10 seconds
    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table")))

    html_content = driver.page_source
    soup = BeautifulSoup(html_content, 'html.parser')

    # Step 3: Locate the table you want to scrape
    table = soup.find('div', class_='table-scroll').find('table')
    # Step 4: Read the HTML table into a DataFrame
    df = pd.read_html(StringIO(str(table)))[0]

    # Step 5: Display the DataFrame
    driver.quit()
    dk_results = df.iloc[:, [1, 2, 6, 7, 8, 10, 11, 12, 13, -3]].copy()
    dk_results.columns = ['players', 'Team', 'Hits', 'Singles', 'Doubles', 'Home Runs', 'Runs Scored', 'RBIs', 'Walks', 'Stolen Bases']
    dk_results['Hits + Runs + RBIs'] = dk_results['Hits'] + dk_results['Runs Scored'] + dk_results['RBIs']
    triples = dk_results['Hits'] - dk_results['Singles'] - dk_results['Doubles'] - dk_results['Home Runs']
    dk_results['Total Bases'] = dk_results['Singles'] + dk_results['Doubles'] * 2 + dk_results['Home Runs'] * 4 + triples * 3
    dk_results = dk_results.melt(id_vars = ['players', 'Team'],
             var_name = 'bet_type',
             value_name='value')
    return dk_results