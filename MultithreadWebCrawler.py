import time

import requests
import multiprocessing
import pickle
import json
import os
from bs4 import BeautifulSoup
from bs4.element import Comment
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class MultiThreadCrawler:
    def __init__(self, base_url, depth):
        self.base_url = base_url
        extracted_url = urlparse(base_url)
        parent = extracted_url.path[:extracted_url.path.rfind("/") + 1]
        self.root_url = '{}://{}{}'.format(extracted_url.scheme, extracted_url.netloc, parent)
        self.pool = ThreadPoolExecutor(1)
        self.to_crawl = Queue()
        self.to_crawl.put({self.base_url: depth})
        self.stored_folder = Path(os.path.abspath('')).parent / './PageRanking-Service/crawledtestD2/'
        self.service = Service(ChromeDriverManager().install())

        if not Path(self.stored_folder).exists():
            Path.mkdir(self.stored_folder)

        if Path(self.stored_folder / 'url_list.pickle').exists():
            with open(self.stored_folder / 'url_list.pickle', 'rb') as f:
                self.crawled_pages = pickle.load(f)
            print(self.crawled_pages)
        else:
            self.crawled_pages = set([])

    def run_scraper(self):
        while True:
            try:
                target = self.to_crawl.get(timeout=10)
                url, depth = [(k, target[k]) for k in target][0]
                # print(url + self.crawled_pages.pop())
                if url not in self.crawled_pages:
                    self.crawled_pages.add(url)
                    # self.extract_page(self.get_page, url, depth - 1)
                    job = self.pool.submit(self.get_page, url, depth - 1)
                    job.add_done_callback(self.extract_page)
            except Empty:
                with open(self.stored_folder / 'url_list.pickle', 'wb') as f:
                    pickle.dump(self.crawled_pages, f, pickle.HIGHEST_PROTOCOL)
                with open(self.stored_folder / 'url_list.pickle', 'rb') as f:
                    print(pickle.load(f))
                break
            except Exception as e:
                print(e)
                continue

    def extract_page(self, str):
        if str.result():
            result, url, depth = str.result()
            if result:
                url_lists = self.parse_links(result, depth)
                self.parse_contents(url, result, url_lists)

    def get_page(self, url, depth):
        try:
            with webdriver.Chrome(service=self.service) as driver:
                driver.get(url)
                driver.implicitly_wait(5)
                time.sleep(3)
                res = driver.page_source
                # print(res)
                return res, url, depth
        except requests.RequestException:
            return

    def parse_links(self, html, depth):
        soup = BeautifulSoup(html, 'html.parser')
        links = soup.find_all('a', href=True)
        url_lists = []
        for link in links:
            url = link['href']
            url = urljoin(self.root_url, url)
            if depth >= 0 and '..' not in url and url not in self.crawled_pages:
                print("Adding {}".format(url))
                self.to_crawl.put({url: depth})
            url_lists.append(url)
        return url_lists

    def parse_contents(self, url, html, url_lists):
        def tag_visible(element):
            if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
                return False
            if isinstance(element, Comment):
                return False
            return True

        try:
            soup = BeautifulSoup(html, 'html.parser')
            texts = soup.findAll(text=True)
            visible_texts = filter(tag_visible, texts)

            title = soup.find('title').string.strip()
            text = u" ".join(t.strip() for t in visible_texts).strip()

            with open(self.stored_folder / (str(hash(url)) + '.txt'), 'w', encoding='utf-8') as f:
                json.dump({'url': url, 'title': title, 'text': text, 'url_lists': url_lists}, f, ensure_ascii=False)
        except:
            pass


if __name__ == '__main__':
    s = MultiThreadCrawler("http://localhost:3000/", 2)
    s.run_scraper()
