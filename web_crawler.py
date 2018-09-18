import csv
import os
import shutil
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

class CSVInputError(Exception):
    pass

class WebCrawler:
    def __init__(self, csv_path):
        self.seed, self.num_pages, self.domain = self.get_csv_input(csv_path)
        self.repo_files = {}
        self.file_count = 0
        self.initialize_repo()
        self.initialize_seed()

    def get_csv_input(self, csv_path):
        with open(csv_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')

            file_input = tuple(next(reader))
            if not 2 <= len(file_input) <= 3:
                raise CSVInputError("CSV input must be length 2 or 3")

            if len(file_input) == 2:
                seed, num_pages = file_input
                domain = None
            elif len(file_input) == 3:
                seed, num_pages, domain = file_input
            return seed, num_pages, domain

    def initialize_repo(self):
        self.repo = 'repository'
        if os.path.isdir(self.repo):
            shutil.rmtree(self.repo)
        os.mkdir(self.repo)

    def check_domain(self, domain):
        if self.domain:
            return domain == self.domain
        return True

    def add_file_to_repo(self, url):
        if url not in self.repo_files:
            r = requests.get(url)
            self.file_count += 1
            self.repo_files[url] = f'{self.file_count}.html'
            with open(os.path.join(self.repo, self.repo_files[url]), 'wb') as f:
                f.write(r.content)

    def find_links(self, url):
        with open(os.path.join(self.repo, self.repo_files[url]), 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            links = soup.find_all('a')
            for link in links:
                parsed_url = urlparse(link['href'])
                if parsed_url.scheme and parsed_url.netloc:
                    url = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}'
                    print(url)
                else:
                    parsed_host_url = urlparse(url)
                    url = f'{parsed_host_url.scheme}://{parsed_host_url.netloc}{parsed_url.path}'
                    print(url)

    def initialize_seed(self):
        parsed_url = urlparse(self.seed)
        add_to_repo = self.check_domain(parsed_url.netloc)
        if add_to_repo:
            self.add_file_to_repo(self.seed)
            self.find_links(self.seed)





