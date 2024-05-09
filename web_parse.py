from bs4 import BeautifulSoup
import requests


def fetch_and_parse(url='https://www.fragrantica.com/perfume/Tom-Ford/Ombre-Leather-Parfum-68716.html'):
    # Fetching the webpage content
    session = requests.session()  # When you use a session, it enables you to persist certain parameters such as cookies, headers, and other configuration across requests made using the same session
    headers_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    html_content = session.get(url, headers=headers_agent).text
    html_soup = BeautifulSoup(html_content, 'lxml')
    # Проблема: відповіддю є не вміст шуканої сторінки, а екран завантаження
    # Треба якось приймати інші відповіді в межах request сесії
    print(html_soup.prettify())

    response = requests.get(url)
    response.raise_for_status()  # Raises an HTTPError for bad requests (4xx or 5xx)

    return parse_perfume_page(response.text)


def parse_perfume_page(html_content):
    '''
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

    '''
    soup = BeautifulSoup(html_content, 'lxml')
    # print(soup.prettify())
    # Extracting perfume title
    title = soup.title.text

    # Extracting rating and votes

    # rating_section = soup.find('p', class_='info_note') #{'class': 'info_note'}) # cannot find
    rating_section = soup.find('div', itemprop='aggregateRating')
    #rating_section = soup.find('span', {'class': 'numvote'})
    rating = rating_section.find('span', itemprop='ratingValue').text if rating_section else None
    votes = rating_section.find('span', itemprop='ratingCount').text if rating_section else None

    # # Extracting main accords
    accords = {}
    accord_list = soup.find_all('div', {'class': 'accord-bar'})
    for accord in accord_list:
        name = accord.text.strip()
        percentage = accord.get('style', '').split(':')[-1].strip('%;')
        accords[name] = float(percentage)

    # Extracting season preferences
    seasons = {}
    for i in range(4):
        season = soup.find('div', index=str(i))
        percentage = season.find('div', class_='voting-small-chart-size').find_all('div')[1].get('style', '').split(';')[-3].split(':')[-1].strip('%;')
        seasons[season.text.strip()] = float(percentage)


    # Day/Night preferences
    day_night = {}
    for i in range(2):
        day_or_night = soup.find('div', index=str(4 + i))
        percentage = day_or_night.find('div', class_='voting-small-chart-size').find_all('div')[1].get('style', '').split(';')[-3].split(':')[-1].strip('%;')
        day_night[day_or_night.text.strip()] = float(percentage)



    # Extracting notes
    # yet to be implemented;
    # Проблема: кожний набір нот має довільну кількість div контейнерів (на 3 вглибину) без id або
    # інших розпізнавальних знаків
    # Можливий варіант: три рази ми заглиблюємося через find (або find_all з конкретними значеннями порядку)
    # Повторюівати цю процедуру допоки знайдене значення не None. Але межі пошуку все одно треба якось вказувати.
    # Чи можна шукати додатково по значенням аргументів, або по наявності включних елементів?
    notes = {}
    note_section = soup.find('div', id='pyramid').find_all('h4') # це може слугувати роздільником, який задає межі для пошуку
    for note_block in note_section:
        print(note_block)
        print(note_block.text)  #




    # Gender
    # Price

    return {
        'title': title,
        'rating': rating,
        'votes': votes,
        'accords': accords,
        'seasons': seasons,
        'day_night': day_night
    }

    #     'notes': notes,
    #     'gender': gender,
    #     'price': price
    # }


if __name__ == '__main__':
    with open('Leather Parfume.html', 'r',  encoding="utf8") as html_file:
        content = html_file.read()
        output = parse_perfume_page(content)
        print(output)












# with open('test_1_page.html', 'r') as html_file:
#     content = html_file.read()
#     soup = BeautifulSoup(content, 'lxml')
#     course_cards = soup.find_all('div', class_='card')
#     for course in course_cards:
#         course_name = course.h5.text
#         course_price = course.a.text.split()[-1]
#         print(f'{course_name} costs {course_price}')
#
#
#
