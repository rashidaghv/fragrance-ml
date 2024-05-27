"""
This script retrieves the necessary info from the Fragrantica website about the perfumes.
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
        with webdriver.Chrome() as driver:
            driver.get(perfume_url)
            time.sleep(WAIT_TIME_SELENIUM)

            html_content = driver.page_source
            soup = BeautifulSoup(html_content, 'lxml')

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

                # wait for dynamic content to be loaded (adjust WAIT_TIME_SELENIUM if needed)
                WebDriverWait(driver, WAIT_TIME_SELENIUM).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'voting-small-chart-size'))
                )

                # get the page source after content has loaded (that's the whole point of using Selenium!)
                html_content = driver.page_source
                soup = BeautifulSoup(html_content, 'lxml')

                winter, spring, summer, fall = None, None, None, None
                day, night = None, None

                # extract the seasons
                for i in range(4):
                    try:
                        season = soup.find('div', index=str(i))
                        percentage_div = season.find('div', class_='voting-small-chart-size').find_all('div')[1]
                        percentage_style = percentage_div.get('style', '')
                        percentage = percentage_style.split(';')[-3].split(':')[-1].strip('%;')
                        season_name = season.text.strip()
                        if season_name.lower() == 'winter':
                            winter = float(percentage)
                        elif season_name.lower() == 'spring':
                            spring = float(percentage)
                        elif season_name.lower() == 'summer':
                            summer = float(percentage)
                        elif season_name.lower() == 'fall':
                            fall = float(percentage)
                    except (AttributeError, IndexError) as e:
                        print(f"Error extracting season {i}: {e}")


                # extract day/night
                for i in range(2):
                    try:
                        day_or_night = soup.find('div', index=str(4 + i))
                        percentage_div = day_or_night.find('div', class_='voting-small-chart-size').find_all('div')[1]
                        percentage_style = percentage_div.get('style', '')
                        percentage = percentage_style.split(';')[-3].split(':')[-1].strip('%;')
                        if day_or_night.text.strip().lower() == 'day':
                            day = float(percentage)
                        elif day_or_night.text.strip().lower() == 'night':
                            night = float(percentage)
                    except (AttributeError, IndexError) as e:
                        print(f"Error extracting day/night {i}: {e}")

                driver.quit()

            # catch potential exceptions
            except Exception as e: 
                print(f"An error occurred: {e}")
                if 'driver' in locals():
                    driver.quit()

            # sillage
            largest_category_sillage = None 
            largest_value_sillage = 0

            for grid_row in soup.find_all('div', class_='grid-x grid-margin-x'):
                category_name_element = grid_row.find('span', class_='vote-button-name')
                value_element = grid_row.find('span', class_='vote-button-legend')

                if category_name_element and value_element:
                    try:
                        value = int(value_element.text)
                    except ValueError:  # handle cases where the text is not a valid number
                        continue
            
                    category_name = category_name_element.text

                    if value > largest_value_sillage:
                        largest_category_sillage = category_name
                        largest_value_sillage = value
            
            # longevity
            largest_category_longevity = None 
            largest_value_longevity = 0

            for grid_row in soup.find_all('div', class_='grid-x grid-margin-x'):
                category_name_element = grid_row.find('span', class_='vote-button-name')
                value_element = grid_row.find('span', class_='vote-button-legend')

                if category_name_element and value_element:
                    try:
                        value = int(value_element.text)
                    except ValueError:  # error handling
                        continue
                    category_name = category_name_element.text

                    if value > largest_value_longevity:
                        largest_category_longevity = category_name
                        largest_value_longevity = value


            # inspect the results
            print(f'URL: {perfume_url}')
            print(f'Title: {title}')
            print(f'Rating: {rating}')
            print(f'Number of votes: {num_votes}')
            print(f'Number of reviews: {num_reviews}')
            print(f'Accords: {", ".join(accords)}')
            print(f'Winter: {winter}')
            print(f'Spring: {spring}')
            print(f'Summer: {summer}')
            print(f'Fall: {fall}')
            print(f'Day: {day}')
            print(f'Night: {night}')
            print(f"Sillage: {largest_category_sillage}")
            print(f"Longevity: {largest_category_longevity}")
            print('---')


if __name__ == '__main__':
    start_time = time.time()
    res = scrape_fragrantica(n_displayed=1)
    end_time = time.time()
    print(f"Execution time of the function is: {end_time - start_time} seconds")