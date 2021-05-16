import datetime as dt
import urllib.request
import logging
import requests
from urllib.parse import urlencode

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG, 
                    format="%(asctime)s, %(levelname)s, %(name)s, %(message)s")

URL = 'http://www.cbr.ru/scripts/XML_daily.asp'
DAYS = 90


def get_dates(number_of_days):
    """ Получает список всех дат, начиная с даты "number_of_days" дней назад
    """
    dates = []
    end_date = dt.date.today()
    for day in reversed(range(number_of_days)):
        date = (
            end_date - dt.timedelta(days=day)).strftime('%d/%m/%Y')
        dates.append(date)
    return dates


def get_quotes(date):
    """ Получает XML котировок валют за заданную дату """
    params = {'date_req': date}
    url = URL + '?' + urlencode(params)
    try: 
        response = urllib.request.urlopen(url).read()
    except requests.exceptions.ConnectTimeout as e: 
        logging.error('Время ожидания истекло') 
        raise e
    
    soup = BeautifulSoup(response, 'xml')
    currencies = soup.find_all('Valute')
    return currencies


def parse_quotes(currencies, date):
    """ Выводит доступные котировки валют в формате:
    [   <Валюта1>
        {
            'denomination': <номинал>,
            'name': <наименование>,
            'value': <курс>
        },
        <Валюта2>
        {
            ...
        },
        ...
    ]
    """
    quotes_list = []
    for currency in currencies:
        quote = {}
        # Номинал
        quote['denomination'] = currency.find('Nominal').text
        # Наименование валюты
        quote['name'] = currency.find('Name').text
        # Курс
        quote['value'] = currency.find('Value').text
        # Дата
        quote['date'] = date
        quotes_list.append(quote)
    return quotes_list


def calculate(quotes_list_result):
    """ Вычисляет заданные показатели:
    - значение максимального курса валюты, название этой валюты
      и дату этого максимального значения;
    - значение минимального курса валюты, название этой валюты
      и дату этого минимального значения;
    - среднее значение курса рубля за весь период по всем валютам.
    """
    max_value = 0
    min_value = 1000
    sum_value = 0

    for quote in range(len(quotes_list_result)):
        value = quotes_list_result[quote]['value']
        value = float(value.replace(',', '.'))
        sum_value += value  # Сумма всех курсов для вычисления среднего знач-я
        denomination = int(quotes_list_result[quote]['denomination'])
        normalized_value = value / denomination
        
        # Находим максимальный курс:
        if normalized_value > max_value:
            max_value = normalized_value
            max_date = quotes_list_result[quote]['date']
            max_currency_name = quotes_list_result[quote]['name']

        # Находим минимальный курс:
        if normalized_value < min_value:
            min_value = normalized_value
            min_date = quotes_list_result[quote]['date']
            min_currency_name = quotes_list_result[quote]['name']

    # Вычисляем средний курс:
    average = sum_value / len(quotes_list_result)

    return (
        f'Максимальный курс: {max_value}, {max_currency_name}, {max_date} \n'
        f'Минимальный курс: {min_value}, {min_currency_name}, {min_date} \n'
        f'Средний курс: {average}'
    )


def main():
    try: 
        # Получаем список дат
        dates = get_dates(DAYS)
        # Собираем котировки в результирующий список:
        quotes_list_result = []
        for date in dates:
            currencies = get_quotes(date)
            quotes_list_result += parse_quotes(currencies, date)
        # Печатаем вычисленные значения
        print(calculate(quotes_list_result))
    except Exception as e: 
        logging.error(f'Произошла ошибка: {e}')


if __name__ == '__main__':
    main()
