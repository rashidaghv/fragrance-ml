from bs4 import BeautifulSoup
import requests
import os
import pickle
import time
import selenium  # programmatically control web browsers
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from splinter import Browser
import random
# from seleniumbase import Driver # it can sove captchas given the url (not in browser)
from selenium.webdriver.common.action_chains import ActionChains # allow low-level interactions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re

# webdriver: for a setup process to control a browser in python. ChromeDriverManager handle downloading, updating, and setting up the ChromeDriver executable.
# Splinter - web application testing tool built on top of Selenium. It provides an easy-to-use interface for browser automation and interaction, making it simpler and more Pythonic than using Selenium directly.


file_path = 'scraped_data.pkl'
proxies = []
categories = ['LONGEVITY', 'SILLAGE', 'GENDER', 'PRICE VALUE']



# Why do we need browser? - requests cannot handle modern webpages
# that rely on JavaScript to load the content (dynamic and complex)

def init_browser():
    # Replace the path with your actual path to the chromedriver
    # for some reason binary chrome webdriver doesn't work. Check documentation, which particular path is needed

    # executable_path = {"your_path": ChromeDriverManager().install()}
    # browser = Browser("chrome", **executable_path, headless=False)
    # service = Service(ChromeDriverManager().install())
    # browser = Browser("chrome", service=service, headless=False)
    browser = Browser('firefox', headless=False, incognito=True)
    browser.driver.set_window_size(1200, 800)
    return browser


def random_pause(min_delay=1.5, max_delay=3.5):
    time.sleep(random.uniform(min_delay, max_delay))


def simulate_mouse_movement_simple(driver):
    """Not working"""
    action = ActionChains(driver)
    for _ in range(random.randint(5, 10)):
        x_offset = random.randint(-100, 100)
        y_offset = random.randint(-100, 100)
        action.move_by_offset(x_offset, y_offset).perform()
        random_pause(0.1, 0.5)  # Short random pause between movements


def simulate_human_mouse_movement(driver, start_element, end_element, steps=10):
    """Ця хуйня не працює"""
    action = ActionChains(driver)

    def clamp(value, min_value, max_value):
        return max(min(value, max_value), min_value)

    viewport_width = driver.execute_script("return window.innerWidth")
    viewport_height = driver.execute_script("return window.innerHeight")
    print(viewport_height, viewport_width)

    start_x = clamp(start_element.location['x'] + start_element.size['width'] / 2, 0, viewport_width)
    start_y = clamp(start_element.location['y'] + start_element.size['height'] / 2, 0, viewport_height)
    end_x = clamp(end_element.location['x'] + end_element.size['width'] / 2, 0, viewport_width)
    end_y = clamp(end_element.location['y'] + end_element.size['height'] / 2, 0, viewport_height)

    delta_x = (end_x - start_x) / steps
    delta_y = (end_y - start_y) / steps

    action.move_to_element_with_offset(start_element, start_x, start_y).perform()
    random_pause(0.2, 0.5)

    for i in range(steps):
        offset_x = clamp(delta_x * (i + 1) + random.uniform(-5, 5), 0, viewport_width)
        offset_y = clamp(delta_y * (i + 1) + random.uniform(-5, 5), 0, viewport_height)
        action.move_by_offset(offset_x - start_x, offset_y - start_y).perform()
        start_x, start_y = offset_x, offset_y
        random_pause(0.05, 0.2)

    action.move_to_element(end_element).perform()
    random_pause(0.2, 0.5)


# Function to simulate slow, random scrolling
def random_slow_scroll(browser):
    start_time = time.time()
    scroll_height = browser.execute_script("return document.body.scrollHeight")
    current_position = browser.execute_script("return window.pageYOffset")

    for i in range(random.randint(3,7)):
        scroll_step = random.randint(50, 200)  # Random step size
        current_position += scroll_step
        browser.execute_script(f"window.scrollTo(0, {current_position});")
        random_pause(0.05, 0.15)  # Random pause between steps

        # Check if the end of the page is reached
        if current_position >= scroll_height:
            break
    print("Scroll action took: ", time.time() - start_time)



def crawl_and_parse(year_from, year_to, url='https://www.fragrantica.com/search/'):
    # Search is performed using css selectors (find_by_css) or by Xpath (find_by_xpath)

    browser = init_browser()
    browser.visit(url)
    time.sleep(2)  # to load the page properly

    ### Agree to the privacy notice ###
    try:
        browser.find_by_css('button.css-47sehv').click()
    except Exception as e:
        # if the button is not found (no need to consent) or in case of other unpredictable errors
        print(e, 'An error is in privacy notice consent block')
    time.sleep(2)

    ###  Filtering by release year (for the simplicity of data storing)  ###
    # value: min - 1920, max - 2024

    try:
        browser.find_by_css('input[type="number"]')[0].fill(year_from)
        browser.find_by_css('input[type="number"]')[1].fill(year_to)
    except Exception as e:
        print(e)
        return
    else:
        result1 = browser.find_by_css('input[type="number"]')[0].value
        result2 = browser.find_by_css('input[type="number"]')[0].value
        print(f"Operation successful, new values (first, second): {result1}, {result2} ")

    time.sleep(3)

    ####  CLICK "SHOW MORE RESULTS"  ####
    # (otherwise only 30 can be displayed)

    while True:  # while search is not fully expaneded:
        try:
            button = browser.find_by_xpath(
                '//button[@class="button"and contains(text(),"Show more results")]').first  # xpath expression to locate elements. - XML path query language
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
    print("Perfumes Number:", perfumes_number)

    successful_extractions = 0
    iteration_min = 0
    iteration_max = 0
    parsing_time = 0
    for perfume_iter in range(perfumes_number):
        start_time = time.time()
        try:
            # Trying to access perfume page:
            while True:
                try:
                    # Plan B2 (on top of A1) # same shit #SAAAAAAAAAAAME SHITTTTTTTTTTTTTTTTT
                    # simulate_mouse_movement_simple(browser.driver)
                    # Plan A - immediate action
                    browser.find_by_css('span[class="link-span"]')[perfume_iter].click()
                    # Plan B - human-like behavior # eta parasha ne rabotaet
                    # element_to_click = browser.find_by_css('span[class="link-span"]')[perfume_iter]
                    # simulate_human_mouse_movement(browser.driver, browser.driver.find_element(By.TAG_NAME, 'body'), element_to_click._element)  # Possible improvement: Starting position - last post
                    break
                except selenium.common.exceptions.ElementClickInterceptedException:
                    print("Could not click on the element, use scroll")
                    element_to_click = browser.find_by_css('span[class="link-span"]')[perfume_iter]

                    # Scrolling to the element
                    # Redo for Smooth Scroll
                    try:
                        # arguments[0] refers to the first argument passed to the script, which is element_to_click in this case
                        # Plan A
                        # browser.execute_script("arguments[0].scrollIntoView(true);", element_to_click._element)  # Plan A2 to try: # element = driver.find_element_by_css('div[class*="loadingWhiteBox"]')  # webdriver.ActionChains(driver).move_to_element(element).click(element).perform()
                        # Plan B # not tested yet
                        browser.execute_script("""
                                    #     arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
                                    # """, element_to_click)
                        time.sleep(1)  # Wait for the scroll to complete


                    except Exception as e:
                        print('Error occurred while scrolling:', e)

            random_pause()  # waiting for the page to load completely

            ### I'm a human verification ###
            html_content = browser.html
            html_soup = BeautifulSoup(html_content, 'lxml')

            while html_soup.title.text == "Just a moment...":
                try:
                    browser.find_by_xpath('//iframe[contains(@src, "challenges.cloudflare.com")]').first.click()
                except Exception as e:
                    print(e, 'Could not complete the captcha ')

            # Additional measures to avoid getting blocked:
            # Random smooth scrolling
            random_slow_scroll(browser)

            # browser.execute_script("""
            #     arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
            # """, element)
            # time.sleep(1)  # Wait for the scroll to complete


            # Random mouse actions (maybe on the back button)??


            # Simulate human-like mouse movement
            # action = ActionChains(browser)
            # action.move_to_element(element_to_click).perform()
            # random_pause(0.5, 1.5)  # Short pause before clicking





            # parsing the page
            parse_result = parse_perfume_page(browser.html)
            random_pause() #5
            browser.back()
            random_pause() #3

        except Exception as e:
            print("Exception while extracting data occured:", e)
            print("Successful Extractions:", successful_extractions)
            print(f"Iteration times: Average - {parsing_time/successful_extractions}; Max - {iteration_max}; min - {iteration_min}")
            return

        successful_extractions += 1
        iteration_elapsed_time = time.time() - start_time
        print(f"Iteration {perfume_iter + 1} took {iteration_elapsed_time}")
        parsing_time += iteration_elapsed_time
        iteration_max = max(iteration_max, iteration_elapsed_time)
        if perfume_iter == 0:
            iteration_min = iteration_max
        else:
            iteration_min = min(iteration_min, iteration_elapsed_time)

    print("Search: success!")
    print(f"Iteration times: Average - {parsing_time/successful_extractions}; Max - {iteration_max}; min - {iteration_min}")

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
    # print(title, rating, votes)
    # # Extracting main accords
    accords = {}
    accord_list = soup.find_all('div', {'class': 'accord-bar'})
    for accord in accord_list:
        name = accord.text.strip()
        percentage = accord.get('style', '').split(':')[-1].strip('%;')
        accords[name] = float(percentage)
        # print(name, percentage)

    # Extracting season preferences
    seasons = extract_season(soup)
    #print(seasons)

    # Day/Night preferences
    day_night = extract_day_night(soup)
    #print(day_night)

    # Extracting Longevity, Sillage, Gender, Price to value ratio
    results_long_sill_gend_pv = extract_long_sill_gend_pv(soup)
    #print(results_long_sill_gend_pv)

    # Extracting notes
    top_notes, middle_notes, base_notes = parse_fragrance_notes(soup)
    #print(top_notes, middle_notes, base_notes)

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


def extract_season(soup):
    """
    Parse fragrance features - season usage suitability
    @param soup: soup object
    @return: dict which contain the percentage value of season suitability with keys 'winter', 'spring', 'summer', 'fall'
    """
    seasons = {}
    for i in range(4):
        try:
            season = soup.find('div', index=str(i))
            percentage = \
                season.find('div', class_='voting-small-chart-size').find_all('div')[1].get('style', '').split(';')[
                    -3].split(
                    ':')[-1].strip('%;')
            seasons[season.text.strip().lower()] = float(percentage)
        except Exception as e:     #
            print(f"Error extracting season {i}: {e}")
    return seasons


def extract_day_night(soup):
    """
    Parse fragrance features - night/day usage suitability
    @param soup: soup object
    @return: dict wich contain the percentage value of suitability with keys 'day', 'night'
    """
    day_night = {}
    for i in range(2):
        try:
            day_or_night = soup.find('div', index=str(4 + i))
            percentage = \
                day_or_night.find('div', class_='voting-small-chart-size').find_all('div')[1].get('style', '').split(
                    ';')[
                    -3].split(':')[-1].strip('%;')
            day_night[day_or_night.text.strip().lower()] = float(percentage)
        except Exception as e: # AttributeError, IndexError
            print(f"Error extracting day/night {i}: {e}")
    return day_night


def extract_long_sill_gend_pv(soup):
    """ Parse fragrance features like Longevity, Sillage, Gender, Price/Value from the BeautifulSoup object."""
    # N.B. These features have similar structure, that's why the for-loop was used
    # TODO: what if the values of several categories are the same?

    categories = ['LONGEVITY', 'SILLAGE', 'GENDER', 'PRICE VALUE']
    results = {category: None for category in categories}

    for category in categories:
        category_span = soup.find('span', text=category, attrs={'style': 'font-size: small;'})
        if category_span:
            first_div = category_span.find_parent('div')
            if first_div:
                third_div = first_div.find_next_sibling('div').find_next_sibling('div')
                if third_div:
                    largest_value = 0
                    largest_category = None
                    for grid_row in third_div.find_all('div', class_='grid-x grid-margin-x'):
                        category_name_element = grid_row.find('span', class_='vote-button-name')
                        value_element = grid_row.find('span', class_='vote-button-legend')

                        if category_name_element and value_element:
                            try:
                                value = int(value_element.text)
                            except ValueError:  # error handling
                                continue
                            category_name = category_name_element.text

                            if value > largest_value:
                                largest_category = category_name
                                largest_value = value
                    results[category] = largest_category
    return results

def extract_notes(note_div):
    """Extract notes from a note div."""
    notes_list = []
    note_divs = note_div.find_all("div")
    for i in range(2, len(note_divs), 3):
        notes_list.append(note_divs[i].get_text())
    return notes_list


def parse_fragrance_notes(soup):
    """Parse fragrance notes from the BeautifulSoup object."""
    note_style = "display: flex; justify-content: center; text-align: center; flex-flow: wrap; align-items: flex-end; padding: 0.5rem;"
    notes = soup.find_all("div", attrs={"style": note_style})

    top_notes_list = []
    middle_notes_list = []
    base_notes_list = []

    if len(notes) == 3:
        top_notes_list = extract_notes(notes[0])
        middle_notes_list = extract_notes(notes[1])
        base_notes_list = extract_notes(notes[2])
    elif len(notes) == 2:
        top_notes_list = extract_notes(notes[0])
        middle_notes_list = extract_notes(notes[1])
    elif len(notes) == 1:
        middle_notes_list = extract_notes(notes[0])

    return top_notes_list, middle_notes_list, base_notes_list



if __name__ == '__main__':
    crawl_and_parse(1939, 1939)

    # with open('Leather Parfume.html', 'r', encoding="utf8") as html_file:
    #     content = html_file.read()
    #     output = parse_perfume_page(content)
    #     print(output)
    # https://www.fragrantica.com/perfume/Tom-Ford/Ombre-Leather-Parfum-68716.html
