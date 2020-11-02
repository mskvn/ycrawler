import argparse
import asyncio
import logging
import os.path
import time

import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup

SITE_URL = 'https://news.ycombinator.com/'
ITEM_URL = f'{SITE_URL}item?id=%d'

NEWS_LIMIT = 30
WAIT_TIME_BETWEEN_LOOPS = 60


def parse_args():
    parser = argparse.ArgumentParser(description='Parse news from news.ycombinator.com')
    parser.add_argument('--path', type=str,
                        help='save news there')
    return parser.parse_args()


async def get_and_save(url, path, file_name):
    logging.debug(f'Get content by url {url}')
    async with ClientSession() as session:
        async with session.get(url) as response:
            try:
                response_text = await response.text()
                with open(os.path.join(path, file_name), mode='x') as f:
                    f.write(response_text)
            except Exception:
                logging.error(f'Get error when try fetch url {url}')


async def get_comments(path, item_id):
    logging.debug(f'Get comments for news with id {item_id}')
    item_url = ITEM_URL % int(item_id)
    html_text = requests.get(item_url).text
    links = find_link_from_comments(html_text)
    for name, link in links.items():
        await get_and_save(link, path, f'comment_{name}.html')


def find_link_from_comments(html_text):
    links = dict()
    soup = BeautifulSoup(html_text, 'html.parser')
    comments = soup.find("table", {'class': 'comment-tree'}).find_all('tr', {'class': 'athing comtr'})
    for comment in comments:
        comment_id = comment.get('id')
        comment_text = comment.find('div', {'class': 'comment'}).find('span')
        if not comment_text:
            continue
        links_el = comment_text.find_all('a')
        if len(links_el) != 0:
            for i in range(len(links_el)):
                links[f'{comment_id}_{i}'] = links_el[i].get('href')
    return links


def find_news_items(html_text):
    soup = BeautifulSoup(html_text, 'html.parser')
    return soup.find("table", {'class': 'itemlist'}).find_all("tr", {'class': 'athing'}, limit=NEWS_LIMIT)


def crawl(path):
    while True:
        logging.info(f'Start load news from {SITE_URL}')
        loop = asyncio.get_event_loop()
        tasks = []

        html_text = requests.get(SITE_URL).text
        news_items = find_news_items(html_text)
        logging.info(f'Find {len(news_items)} news')
        for item in news_items:
            news_path = os.path.join(path, item.get('id'))
            if os.path.isdir(news_path):
                logging.info(f"News {item.get('id')} already saved")
                continue
            os.mkdir(news_path)
            url = item.find('a', {'class': 'storylink'}).get('href')
            tasks.append(asyncio.ensure_future(get_and_save(url, news_path, 'news.html')))
            tasks.append(asyncio.ensure_future(get_comments(news_path, item.get('id'))))
        if tasks:
            loop.run_until_complete(asyncio.wait(tasks))
        logging.info('All news and comments loaded')
        logging.info('Wait new news')
        time.sleep(WAIT_TIME_BETWEEN_LOOPS)


def main():
    try:
        args = parse_args()
        logging.basicConfig(format='[%(asctime)s] %(levelname).1s %(message)s',
                            datefmt='%Y.%m.%d %H:%M:%S',
                            level=logging.INFO
                            )
        logging.info('Crawler starting... Press ctrl+C for stop')
        crawl(args.path)
    except Exception:
        logging.exception("Exception occurred")


if __name__ == "__main__":
    main()
