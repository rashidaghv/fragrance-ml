"""
This script scrapes the Fragrantica website to retrieve information about perfumes.
"""
import time

import pandas as pd
from bs4 import BeautifulSoup
from requests_futures.sessions import FuturesSession  # for asynchronous requests
from concurrent.futures import as_completed


def scrape_fragrantica(main_url='https://www.fragrantica.com/search/', headers={'User-Agent': 'Mozilla/5.0'}, n_displayed=3):
    """
    Scrapes Fragrantica website to retrieve information about perfumes and stores it in a DataFrame.

    Parameters:
        main_url (str): The main URL of the Fragrantica website. Default is 'https://www.fragrantica.com/search/'.
        headers (dict): The headers to be used in the HTTP request. Default is {'User-Agent': 'Mozilla/5.0'}.
        n_displayed (int): The number of perfumes to display information for. Default is 3.

    Returns:
        pandas.DataFrame: A DataFrame containing the scraped information.
    """   
    session = FuturesSession()
    response = session.get(main_url, headers=headers).result()

    soup = BeautifulSoup(response.text, 'html.parser')

    perfume_urls = [main_url + a['href'] for a in soup.select('div.cell.card.fr-news-box a')[:n_displayed]]

    # scrape the required information for the first n_displayed perfumes
    futures = [session.get(perfume_url, headers=headers) for perfume_url in perfume_urls]

    data = []
    for future in as_completed(futures):
        response = future.result()

        soup = BeautifulSoup(response.text, 'html.parser')

        rating_element = soup.select_one('span[itemprop="ratingValue"]')
        rating = rating_element.text if rating_element is not None else 'No rating'

        num_votes_element = soup.select_one('span[itemprop="ratingCount"]')
        num_votes = num_votes_element.text if num_votes_element is not None else 'No votes'

        num_reviews_element = soup.select_one('meta[itemprop="reviewCount"]')
        num_reviews = num_reviews_element['content'] if num_reviews_element is not None else 'No reviews'

        accords = [div.text for div in soup.select('div.accord-bar')]

        data.append({
            'Rating': rating,
            'Number of votes': num_votes,
            'Number of reviews': num_reviews,
            'Accords': ', '.join(accords)
        })

    df = pd.DataFrame(data)

    return df


if __name__ == '__main__':
    start_time = time.time()
    res = scrape_fragrantica()
    end_time = time.time()
    print(f"Execution time of the function is: {end_time - start_time} seconds")
    print(res)