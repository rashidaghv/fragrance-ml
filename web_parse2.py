"""
This script retrieves the necessary info from the Fragrantica website.
"""
import time

import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver  # selenium is used, since the page is loaded dynamically
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# constants
WAIT_TIME_SELENIUM = 5  # feel free to test and adjust this value


def scrape_fragrantica(main_url='https://www.fragrantica.com/search/', headers={'User-Agent': 'Mozilla/5.0'}, n_displayed=3):
    """
    Scrapes Fragrantica website to retrieve information about perfumes.
    Prints the info for the first n_displayed perfumes.

    Parameters:
        main_url (str): The main URL of the Fragrantica website. Default is 'https://www.fragrantica.com/search/'.
        headers (dict): The headers to be used in the HTTP request. Default is {'User-Agent': 'Mozilla/5.0'}.
        n_displayed (int): The number of perfumes to display information for. Default is 3.
    """   
    response = requests.get(main_url, headers=headers)

    soup = BeautifulSoup(response.text, 'html.parser')

    perfume_urls = [main_url + a['href'] for a in soup.select('div.cell.card.fr-news-box a')[:n_displayed]]

    # scrape the required information for the first 3 perfumes
    for perfume_url in perfume_urls:
        response = requests.get(perfume_url, headers=headers)

        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.text

        rating_element = soup.select_one('span[itemprop="ratingValue"]')
        rating = rating_element.text if rating_element is not None else 'No rating'

        num_votes_element = soup.select_one('span[itemprop="ratingCount"]')
        num_votes = num_votes_element.text if num_votes_element is not None else 'No votes'

        num_reviews_element = soup.select_one('meta[itemprop="reviewCount"]')
        num_reviews = num_reviews_element['content'] if num_reviews_element is not None else 'No reviews'

        accords = [div.text for div in soup.select('div.accord-bar')]
        
        url = perfume_url

        try:
            driver = webdriver.Chrome()  
            driver.get(url)

            # wait for dynamic content to load (adjust wait_time if needed)
            WebDriverWait(driver, WAIT_TIME_SELENIUM).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'voting-small-chart-size'))
            )

            # get the page source after content has loaded (that's the whole point of using Selenium!)
            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'lxml')

            seasons = {}
            for i in range(4):
                try:
                    season = soup.find('div', index=str(i))
                    percentage_div = season.find('div', class_='voting-small-chart-size').find_all('div')[1]
                    percentage_style = percentage_div.get('style', '')
                    percentage = percentage_style.split(';')[-3].split(':')[-1].strip('%;')
                    seasons[season.text.strip()] = float(percentage)
                except (AttributeError, IndexError) as e:
                    print(f"Error extracting season {i}: {e}")

            day_night = {}
            for i in range(2):
                try:
                    day_or_night = soup.find('div', index=str(4 + i))
                    percentage_div = day_or_night.find('div', class_='voting-small-chart-size').find_all('div')[1]
                    percentage_style = percentage_div.get('style', '')
                    percentage = percentage_style.split(';')[-3].split(':')[-1].strip('%;')
                    day_night[day_or_night.text.strip()] = float(percentage)
                except (AttributeError, IndexError) as e:
                    print(f"Error extracting day/night {i}: {e}")

            driver.quit()

        # catch potential exceptions
        except Exception as e: 
            print(f"An error occurred: {e}")
            if 'driver' in locals():
                driver.quit()

        # inspect the extracted data
        print(f'URL: {perfume_url}')
        print(f'Title: {title}')
        print(f'Rating: {rating}')
        print(f'Number of votes: {num_votes}')
        print(f'Number of reviews: {num_reviews}')
        print(f'Accords: {", ".join(accords)}')
        print(f'Seasons: {seasons}')
        print(f'Day_night: {day_night}')
        print('---')


if __name__ == '__main__':
    start_time = time.time()
    res = scrape_fragrantica(n_displayed=2)
    end_time = time.time()
    print(f"Execution time of the function is: {end_time - start_time} seconds")