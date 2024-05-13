"""
This script scrapes the Fragrantica website to retrieve information about perfumes.
"""
import time

import requests
from bs4 import BeautifulSoup


def scrape_fragrantica(main_url='https://www.fragrantica.com/search/', headers={'User-Agent': 'Mozilla/5.0'}, n_displayed=3):
    """
    Scrapes Fragrantica website to retrieve information about perfumes.
    Prints the info for the first 3 perfumes.

    Parameters:
        main_url (str): The main URL of the Fragrantica website. Default is 'https://www.fragrantica.com/search/'.
        headers (dict): The headers to be used in the HTTP request. Default is {'User-Agent': 'Mozilla/5.0'}.
        n_displayed (int): The number of perfumes to display information for. Default is 3.

    Returns:
        None
    """   
    response = requests.get(main_url, headers=headers)

    soup = BeautifulSoup(response.text, 'html.parser')

    perfume_urls = [main_url + a['href'] for a in soup.select('div.cell.card.fr-news-box a')[:n_displayed]]

    # scrape the required information for the first 3 perfumes
    for perfume_url in perfume_urls:
        response = requests.get(perfume_url, headers=headers)

        soup = BeautifulSoup(response.text, 'html.parser')

        rating_element = soup.select_one('span[itemprop="ratingValue"]')
        rating = rating_element.text if rating_element is not None else 'No rating'

        num_votes_element = soup.select_one('span[itemprop="ratingCount"]')
        num_votes = num_votes_element.text if num_votes_element is not None else 'No votes'

        num_reviews_element = soup.select_one('meta[itemprop="reviewCount"]')
        num_reviews = num_reviews_element['content'] if num_reviews_element is not None else 'No reviews'

        accords = [div.text for div in soup.select('div.accord-bar')]

        # inspect the extracted data
        print(f'URL: {perfume_url}')
        print(f'Rating: {rating}')
        print(f'Number of votes: {num_votes}')
        print(f'Number of reviews: {num_reviews}')
        print(f'Accords: {", ".join(accords)}')
        print('---')


if __name__ == '__main__':
    start_time = time.time()
    scrape_fragrantica()
    end_time = time.time()
    print(f"Execution time of the function is: {end_time - start_time} seconds")