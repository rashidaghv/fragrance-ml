from bs4 import BeautifulSoup
import requests
import os
import pickle
import time
import selenium  # programmatically control web browsers
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from splinter import Browser
from seleniumbase import Driver # it can sove captchas given the url (not in browser)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re

# webdriver: for a setup process to control a browser in python. ChromeDriverManager handle downloading, updating, and setting up the ChromeDriver executable.
# Splinter - web application testing tool built on top of Selenium. It provides an easy-to-use interface for browser automation and interaction, making it simpler and more Pythonic than using Selenium directly.


file_path = 'scraped_data.pkl'
proxies = []

# Why do we need browser? - requests cannot handle modern webpages
# that rely on JavaScript to load the content (dynamic and complex)


def init_browser():
    # Replace the path with your actual path to the chromedriver
    # for some reason binary chrome webdriver doesn't work. Check documentation, which particular path is needed

    # executable_path = {"your_path": ChromeDriverManager().install()}
    # browser = Browser("chrome", **executable_path, headless=False)
    service = Service(ChromeDriverManager().install())
    browser = Browser("chrome", service=service, headless=False)
    return browser


def crawl_and_parse(url='https://www.fragrantica.com/search/'):
    # Search is performed using css selectors (find_by_css) or by Xpath (find_by_xpath)

    browser = init_browser()
    browser.visit(url)
    time.sleep(2) # to load the page properly

    ### Agree to the privacy notice ###
    try:
        browser.find_by_css('button.css-47sehv').click()
    except Exception as e:
        # if the button is not found (no need to consent) or in case of other unpredictable errors
        print(e, 'An error is in privacy notice consent block')
    time.sleep(2)

    ### Filtering by release year (for the simplicity of data storing)###
    # value: min - 1920, max - 2024

    try:
        browser.find_by_css('input[type="number"]')[0].fill(1939)
        browser.find_by_css('input[type="number"]')[1].fill(1939)
    except Exception as e:
        print(e)
        return
    else:
        result1 = browser.find_by_css('input[type="number"]')[0].value
        result2 = browser.find_by_css('input[type="number"]')[0].value
        print(f"Operation successful, new values (first, second): {result1}, {result2} ")

    time.sleep(5)

    ####  CLICK "SHOW MORE RESULTS"  ####(otherwise only 30 can be displayed)
    search_is_expaneded = False
    while True: #not search_is_expaneded:
        try:
            button = browser.find_by_xpath('//button[@class="button"and contains(text(),"Show more results")]').first  # xpath expression to locate elements. - XML path query language
            if 'disabled' in button['outerHTML']:
                print('\"Show more results button\" is disabled')
                break

            print(browser.find_by_xpath('//button[@class="button" and contains(text(),"Show more results")]').first.text)
            button.click()
        except Exception as e:
            print(e)
            break
        else:
            print("\"Show more results button\" was pressed successfully")

    html_content = browser.html
    html_soup = BeautifulSoup(html_content, 'lxml')

    perfumes_number = len(html_soup.select('div.cell.card.fr-news-box a'))
    for k in range(perfumes_number):
        browser.find_by_css('span[class="link-span"]')[0].click()
        time.sleep(5)

        html_content = browser.html
        html_soup = BeautifulSoup(html_content, 'lxml')

        ### I'm a human verification ###
        # if html_soup.title.text == "Just a moment...":
        while html_soup.title.text == "Just a moment...":
            try:
                browser.find_by_xpath('//iframe[contains(@src, "challenges.cloudflare.com")]').first.click()
            except Exception as e:
                print(e, 'Could not complete the captcha ')

            html_content = browser.html
            html_soup = BeautifulSoup(html_content, 'lxml')
            time.sleep(20)

        parse_result = parse_perfume_page(browser.html)
        time.sleep(5)
        browser.back()
        time.sleep(2)
    # enable this code where you need to look into the html code manually
    # with open('crawl_test_page.html', 'w', encoding='utf-8') as file:
    #      file.write(html_soup.prettify())
    return





def fetch_and_parse(url='https://www.fragrantica.com/search/', n_displayed=100):
    """Fetching the webpage content"""

    if os.path.exists(file_path):
        # Load the data from the file
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
    else:
        # If the file doesn't exist, create an empty dictionary
        data = []

    # # When we use a session, it enables us to persist certain parameters such as cookies, headers, and other configuration across requests made using the same session
    # async_session = FuturesSession()
    # #request_session = requests.session()
    # headers_agent = {
    #     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    # }
    # html_content = async_session.get(url, headers=headers_agent)
    # try:
    #     html_content.raise_for_status()  # Raises an HTTPError for bad requests (4xx or 5xx)
    #
    # html_soup = BeautifulSoup(html_content.text, 'lxml')
    #
    # data = []
    # perfume_urls = [url + a['href'] for a in html_soup.select('div.cell.card.fr-news-box a')[:n_displayed]]
    # futures = [async_session.get(perfume_url, headers=headers_agent) for perfume_url in perfume_urls]
    # for future in as_completed(futures):
    #     response = future.result()
    #     response.raise_for_status()  # Raises an HTTPError for bad requests (4xx or 5xx)
    #     data.append(parse_perfume_page(response.text))
    # Fetching the webpage content

    headers_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    # v1
    session = requests.session()  # When you use a session, it enables you to persist certain parameters such as cookies, headers, and other configuration across requests made using the same session

    html_content = session.get(url, headers=headers_agent, timeout=10).text
    # #v2 (VPN)
    # options = Options()
    # options.headless = True
    # driver = webdriver.Firefox(options=options)
    # driver.get(url)
    # html_content = driver.page_source
    # print(html_content)
    # driver.quit()

    html_soup = BeautifulSoup(html_content, 'lxml')
    perfume_urls = [url + a['href'] for a in html_soup.select('div.cell.card.fr-news-box a')[:n_displayed]]
    print(perfume_urls)
    print(html_soup.prettify())
    success_counter = 0
    retries = 0
    retry_delay = 30  # Initial retry delay in seconds
    interval = 6
    for perfume_url in perfume_urls:
        try:
            response = session.get(perfume_url, headers=headers_agent, timeout=10)
            response.raise_for_status()  # Raises an HTTPError for bad requests (4xx or 5xx)
            data.append(parse_perfume_page(response.text))

        except Exception as e:  # session.exceptions.RequestException
            print(f"Error: {e} on iteration {success_counter}")
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)

            if response.status_code == 429:
                print(f"Received 429 Too Many Requests. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                retries += 1
                continue
        success_counter += 1
        time.sleep(interval)

    return data


def parse_perfume_page(html_content):
    """
    Args:
        html_content:

    Returns:
        dictionary, that contains the values for each of parameters:
        - 'tittle' - tittle of the parfume
        - 'rating' -  of the rating on a 5-point scale
        - 'votes' - total amount of votes': votes
        - 'accords': dictionary, that matches accord name with a percentage of dominance ??
        - 'seasons':  dictionary, that matches season name with a percentage of suitability for given season
        - 'day_night': dictionary, that matches daytime name with a percentage of suitability (day/night occasions)
    #     'notes': notes,
    #     'gender': gender,
    #     'price': price

    """
    soup = BeautifulSoup(html_content, 'lxml')
    # print(soup.prettify())

    # Extracting perfume title
    title = soup.title.text

    # Extracting rating and votes
    rating_section = soup.find('div', itemprop='aggregateRating')
    rating = rating_section.find('span', itemprop='ratingValue').text if rating_section else None
    votes = rating_section.find('span', itemprop='ratingCount').text if rating_section else None
    num_reviews_element = soup.select_one('meta[itemprop="reviewCount"]')
    num_reviews = num_reviews_element['content'] if num_reviews_element else None
    print(title, rating, votes)
    # # Extracting main accords
    accords = {}
    accord_list = soup.find_all('div', {'class': 'accord-bar'})
    for accord in accord_list:
        name = accord.text.strip()
        percentage = accord.get('style', '').split(':')[-1].strip('%;')
        accords[name] = float(percentage)

    # Extracting season preferences
    # seasons = {}
    # for i in range(4):
    #     season = soup.find('div', index=str(i))
    #     print(season)
    #     percentage = season.find('div', class_='voting-small-chart-size').find_all('div')[1].get('style', '').split(';')[-3].split(
    #         ':')[-1].strip('%;')
    #     seasons[season.text.strip()] = float(percentage)
    #
    # # Day/Night preferences
    # day_night = {}
    # for i in range(2):
    #     day_or_night = soup.find('div', index=str(4 + i))
    #     percentage = \
    #     day_or_night.find('div', class_='voting-small-chart-size').find_all('div')[1].get('style', '').split(';')[
    #         -3].split(':')[-1].strip('%;')
    #     day_night[day_or_night.text.strip()] = float(percentage)

    # Extracting notes
    # yet to be implemented;
    # Проблема: кожний набір нот має довільну кількість div контейнерів (на 3 вглибину) без id або
    # інших розпізнавальних знаків
    # Можливий варіант: три рази ми заглиблюємося через find (або find_all з конкретними значеннями порядку)
    # Повторюівати цю процедуру допоки знайдене значення не None. Але межі пошуку все одно треба якось вказувати.
    # Чи можна шукати додатково по значенням аргументів, або по наявності включних елементів?
    notes = {}
    # note_section = soup.find('div', id='pyramid').find_all(
    #     'h4')  # це може слугувати роздільником, який задає межі для пошуку
    # for note_block in note_section:
    #     print(note_block)
    #     print(note_block.text)  #

    # Gender
    # Price

    return {
        'title': title,
        'rating': rating,
        'votes': votes,
        'num_reviews': num_reviews,
        'accords': accords
        # 'seasons': seasons,
        # 'day_night': day_night
    }

    #     'notes': notes,
    #     'gender': gender,
    #     'price': price
    # }


if __name__ == '__main__':
    crawl_and_parse()

    # with open('Leather Parfume.html', 'r', encoding="utf8") as html_file:
    #     content = html_file.read()
    #     output = parse_perfume_page(content)
    #     print(output)
    # https://www.fragrantica.com/perfume/Tom-Ford/Ombre-Leather-Parfum-68716.html
