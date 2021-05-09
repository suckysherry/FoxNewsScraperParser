import re
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from datetime import datetime
from bs4 import BeautifulSoup
import json
import os
import pandas as pd
import logging


def requests_retry_session(url: str):
    """
    Retry to connect the session
    :param url: the url
    :return: the response of the url
    """
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session.get(url)


def get_json_from_api(api_url: str):
    """
    Convert the api content into a json file
    :param api_url: The api address
    :return: a json file
    """
    response = requests_retry_session(api_url)
    js = json.loads(re.search(r'(?<=\()([\s\S]*)(?=\))', response.text).group())
    return js


def get_meta_data_from_json(js: dict, key: str):
    """
    Scrape the publish time, title, description, url and image urls of each article
    :param js: a json file
    :param key: key word that needs to query
    :return: a list containing the meta data
    """
    docs = js['response']['docs']
    meta_data = []
    for doc in docs:
        publish_time = datetime.strptime(doc['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%Y-%m-%d %H:%M:%S')
        title = doc['title']
        description = doc['description']
        url = doc['url'][0]
        if doc['image'] is None:
            images = ''
        else:
            images = '@@@'.join([img['url'] for img in doc['image']])
        meta_data.append([publish_time, title, description, url, images, key])
    return meta_data


def parse_text(url: str, title: str):
    """
    Parse the html of the article
    :param url: the url
    :param title: the title of the article
    :return: a string that contains the article tile and the article body
    """
    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    texts = soup.body.find('article').find_all('p')
    paragraphs = ['Title:', title, '*' * 20, 'Body:']
    for content in texts:
        paragraphs.append(content.get_text())
    return '\n'.join(paragraphs)


def download_img(url: str, date: str, index: int, number: int):
    """
    Download the images from the image url
    :param url: the image url
    :param date: the publish time
    :param index: the index of the article in the summary
    :param number: the rank of the image in one article
    :return: No return
    """
    response = requests.get(url)
    if not os.path.exists('./Content/Images'):
        os.makedirs('./Content/Images')
    with open('./Content/Images/{}{}_{}.png'.format(date, index, number), 'wb') as f:
        f.write(response.content)


def download_html(url: str, date: str, index: int):
    """
    Download the htmls from the image url
    :param url: the html url
    :param date: the publish time
    :param index: the index of the article in the summary
    :return: No return
    """
    html = requests.get(url).content
    if not os.path.exists('./Content/HTMLs/'):
        os.makedirs('./Content/HTMLs')
    with open('./Content/HTMLs/{}{}.html'.format(date, index), 'wb') as f:
        f.write(html)


def download_txt(title: str, url: str, date: str, index: int):
    """
    Download the texts from the image url
    :param title: the article title
    :param url: the html url
    :param date: the publish time
    :param index: the index of the article in the summary
    :return: No return
    """
    text = parse_text(url, title)
    if not os.path.exists('./Content/Articles'):
        os.makedirs('./Content/Articles')
    try:
        with open('./Content/Articles/{}{}.txt'.format(date, index), 'w') as f:
            f.write(text)
    except Exception as e:
        print(e)
        text = text.encode('utf-8')
        with open('./Content/Articles/{}{}.txt'.format(date, index), 'w') as f:
            f.write(text)


class Scraper:

    def __init__(self, start_date: str, end_date: str, keywords: list, logger: logging.Logger):
        """
        Initialize the start date, end data and key words and define the API structure
        :param start_date: the start date of scraping the data
        :param end_date: the end date of scraping the data
        :param keywords: the key words that need to query
        """
        self.api_url = "https://api.foxnews.com/v1/content/search?q={0}&fields=date,description,title,url,image,type," \
                       "taxonomy&sort=latest&section.path=fnc&type=article&min_date={1}&max_date={2}&start={" \
                       "3}&callback=angular.callbacks._{4}"
        self.start_date = datetime.strptime(start_date, "%Y%m%d")
        self.end_date = datetime.strptime(end_date, "%Y%m%d")
        self.keywords = keywords
        self.logger = logger

    def scrape_save_meta_data(self):
        """
        Scrape the title, description, url and image urls of the articles
        :return: No return. The file is saved at ./summary/ folder
        """
        if not os.path.exists('./summary/'):
            os.makedirs('./summary/')
        date_index = pd.date_range(self.start_date, self.end_date, freq='1D')
        for day in date_index:
            self.logger.info('Scrape and save meta data of {}'.format(day))
            summary_list = []
            for key in self.keywords:
                self.logger.info('Query key word: {}'.format(key))
                page_number = 0
                article_start_index = 1
                meta_data = []
                while meta_data or (page_number == 0):
                    api = self.api_url.format(key, day.strftime('%Y-%m-%d'), day.strftime('%Y-%m-%d'),
                                              article_start_index, page_number)
                    page_number += 1
                    article_start_index = page_number * 10 + 1
                    try:
                        js = get_json_from_api(api)
                        meta_data = get_meta_data_from_json(js, key)
                        summary_list.extend(meta_data)
                    except Exception:
                        self.logger.error('Failed to get json file from the api: {}'.format(api), exc_info=True)
                        continue
            df_summary = pd.DataFrame(summary_list, columns=['datetime', 'title', 'description', 'url', 'image_urls',
                                                             'search_key_word'])
            df_summary.drop_duplicates(subset=['url'], inplace=True)
            df_summary.to_csv('./summary/summary_{}.csv'.format(day.strftime('%Y%m%d')), index=False,
                              encoding='utf-8')


class Parser(Scraper):
    def __init__(self, start_date: str, end_date: str, keywords: list, logger: logging.Logger):
        super(Parser, self).__init__(start_date, end_date, keywords, logger)

    def parse_download_articles(self):
        """
        Parse the html of articles and save the text and images in the folder ./Content/
        :return: No return
        """
        date_index = pd.date_range(self.start_date, self.end_date, freq='1D')
        for day in date_index:
            self.logger.info('Parse and download articles and images of {}'.format(day))
            date = day.strftime('%Y%m%d')
            summary_path = './summary/summary_{}.csv'.format(date)
            if os.path.exists(summary_path):
                df_summary = pd.read_csv('./summary/summary_{}.csv'.format(date))
                df_summary.fillna('', inplace=True)
            else:
                self.logger.warning('CSV file summary_{}.csv does not exist!'.format(date))
                print('CSV file summary_{}.csv does not exist!'.format(date))
                continue
            if df_summary.empty:
                self.logger.warning('CSV file summary_{}.csv is empty!'.format(date))
                print('CSV file summary_{}.csv is empty!'.format(date))
                continue
            else:
                for index in df_summary.index:
                    title = df_summary.loc[index, 'title']
                    url = df_summary.loc[index, 'url']
                    image_urls = df_summary.loc[index, 'image_urls'].split('@@@@@')
                    try:
                        download_txt(title, url, date, index)
                        download_html(url, date, index)
                    except Exception:
                        self.logger.error('Failed to download the article and html of the url: {}'.format(url),
                                          exc_info=True)
                        pass
                    for i in range(len(image_urls)):
                        try:
                            download_img(image_urls[i], date, index, i)
                        except Exception:
                            self.logger.error('Failed to download the image of the url: {}'.format(image_urls[i]),
                                              exc_info=True)
                            continue
