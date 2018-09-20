import csv
import os
import shutil
import requests
import time
import fnmatch
import sys
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from queue import Queue
from IPython.display import display, HTML

class CSVInputError(Exception):
    pass

class InputError(Exception):
    pass

class WebCrawler:
    '''
    Can be initialized with a csv file containing one 2 or 3 length line OR
        with kwargs
    Params: seed, num_pages, domain
    '''
    def __init__(self, csv_path=None, **kwargs):
        if csv_path:
            seed, num_pages, domain = self.get_csv_input(csv_path)
        else:
            seed, num_pages, domain = self.get_kwarg_input(kwargs)
        num_pages = self.validate_input(seed, num_pages, domain)

        self.seed, self.num_pages, self.domain = seed, num_pages, domain
        self.repo_files = {}
        self.file_count = 0
        self.main_link_queue = set()
        self.domain_dict = {}
        self.visited_robots = set()

        self.initialize_repo()
        self.initialize_seed()
        self.process_main_link_queue()

    def get_csv_input(self, csv_path):
        '''
        Gets input from csv file
        Checks that input is correct length
        '''
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

    def get_kwarg_input(self, kwargs):
        '''
        Gets input from kwargs
        Checks for all applicable inputs
        '''
        for kw in ['seed', 'num_pages', 'domain']:
            if kw not in kwargs:
                raise(InputError('kwargs must include seed, num_pages, and domain'))
        return kwargs['seed'], kwargs['num_pages'], kwargs['domain']

    def validate_input(self, seed, num_pages, domain):
        '''
        Validates that seed and domain are strings,
            that num_pages is int (and coerces it),
            that seed is a valid url
        '''
        if not isinstance(seed, str):
            raise InputError('seed input must be a string')
        if not isinstance(domain, str):
            raise InputError('domain input must be a string')
        try:
            num_pages = int(num_pages)
        except ValueError as e:
            raise InputError('num_pages input is invalid. Must be coercible to int')

        seed_parse = urlparse(seed)
        if not (seed_parse.scheme and seed_parse.netloc):
            raise InputError("Seed input is invalid url")

        return num_pages

    def initialize_repo(self):
        '''
        If repository exists from previous run, it is deleted
        Creates repository
        '''
        self.repo = 'repository'
        if os.path.isdir(self.repo):
            shutil.rmtree(self.repo)
        os.mkdir(self.repo)

    def initialize_seed(self):
        '''
        Calls process url on seed url
        '''
        self.process_url(self.seed)

    def process_url(self, url):
        '''
        Checks if a robot exists for url
        Checks if the url is in the domain input
        Gets url and adds file to repository
        Finds links from file and adds them to main_link_queue
        '''
        crawl_delay = self.check_for_robot(url)
        parsed_url = urlparse(url)
        add_to_repo = self.check_domain(parsed_url.netloc)
        if add_to_repo:
            time.sleep(crawl_delay)
            self.add_file_to_repo(url)
            self.find_links(url)

    def process_main_link_queue(self):
        '''
        process entire main_link_queue into a dictionary organized by domain (domain_dict)
        Per domain, calls process_url on each url
        Recurses if there are still urls in main_link_queue and the file_count has not been met
        TODO: domain check so we don't bother processing other domains
        '''
        while bool(self.main_link_queue):
            link = self.main_link_queue.pop()

            parsed_link = urlparse(link)
            if parsed_link.netloc not in self.domain_dict and link not in self.repo_files:
                self.domain_dict[parsed_link.netloc] = set()
                self.domain_dict[parsed_link.netloc].add(link)
            elif parsed_link.netloc in self.domain_dict and link not in self.repo_files:
                self.domain_dict[parsed_link.netloc].add(link)

        # Threading would be awesome here
        for domain in self.domain_dict:
            for url in self.domain_dict[domain]:
                if self.check_file_count():
                    self.process_url(url)
                else:
                    return

        if bool(self.main_link_queue) and self.check_file_count():
            self.process_main_link_queue()

    def check_for_robot(self, url):
        '''
        Checks if the robot has been visited for the url
        If not, gets the robot.txt file for the url's domain
            Finds disallowed urls
            Finds sitemap, if any
            Removes disallowed urls from sitemap urls
            Finds crawl delay, if any and sets it
        TODO: case where site does not have robots.txt
        TODO: save crawl_delay for visited robots
        TODO: follow sub sitemaps to valid urls (case: reddit)
        '''
        parsed_url = urlparse(url)
        base_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
        crawl_delay = 10
        if base_url not in self.visited_robots:
            robots = f'{base_url}/robots.txt'
            r = requests.get(robots)
            tmp = {}
            text = [line.decode('utf-8') for line in r.iter_lines()]

            for i,line in enumerate(text):
                if 'user-agent' in line.lower():
                    tmp[line.lower()] = i
                elif 'Sitemap' in line:
                    tmp[line] = i
                # print(line)

            # print(tmp)

            user_line = tmp['user-agent: *']
            others = sorted(list(set(tmp.values()) - set([user_line])))
            end_user = others[0] if others else None

            user_agent = {'Disallow': [], 'Crawl-delay': None}
            for i,line in enumerate(text):
                if i < user_line:
                    pass
                elif i > end_user:
                    pass
                elif 'Disallow' in line:
                    ext = line.split(' ')[1]
                    user_agent['Disallow'].append(f'{base_url}{ext}')
                elif 'Crawl-delay' in line:
                    user_agent['Crawl-delay'] = int(line.split(' ')[1])

            sitemaps = [key.split(' ')[1] for key in tmp.keys() if 'Sitemap' in key]
            sitemap_urls = []
            for sitemap in sitemaps:
                sr = requests.get(sitemap)
                time.sleep(1)
                sr.encoding = 'utf-8'
                soup = BeautifulSoup(sr.text, 'html5lib')
                locs = soup.find_all("loc")
                sitemap_urls += [t.text for t in locs]

            sitemap_urls = set(sitemap_urls)

            for disallowed in user_agent['Disallow']:
                filtered = fnmatch.filter(sitemap_urls, disallowed)
                sitemap_urls = sitemap_urls - set(filtered)

            self.main_link_queue |= sitemap_urls

            self.visited_robots.add(base_url)

            if user_agent['Crawl-delay']:
                crawl_delay = user_agent['Crawl-delay']

            time.sleep(5)
        return crawl_delay

    def check_domain(self, domain):
        '''
        If class domain input exists, returns False if url domain not equal to it
        In all other cases returns True
        Controls if the url will be hit with a request
        '''
        if self.domain:
            return domain == self.domain
        return True

    def add_file_to_repo(self, url):
        '''
        Gets the url and saves filename and status in repo_files
        Saves file in repository
        TODO: error handling for request and file save
        '''
        if url not in self.repo_files:
            r = requests.get(url)
            self.file_count += 1
            self.repo_files[url] = {'filename': f'{self.file_count}.html', 'status': r.status_code}
            with open(os.path.join(self.repo, self.repo_files[url]['filename']), 'wb') as f:
                f.write(r.content)

    def find_links(self, url):
        '''
        Opens a url's file and finds all links within, and all images
        Saves links to main_link_queue and images to url's repo_files entry
        '''
        with open(os.path.join(self.repo, self.repo_files[url]['filename']), 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
            links = soup.find_all('a')
            self.repo_files[url]['links'] = 0
            for link in links:
                try:
                    parsed_url = urlparse(link['href'])
                    if parsed_url.scheme and parsed_url.netloc:
                        link_url = f'{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}'
                    else:
                        parsed_host_url = urlparse(url)
                        link_url = f'{parsed_host_url.scheme}://{parsed_host_url.netloc}{parsed_url.path}'
                    self.repo_files[url]['links'] += 1
                    self.main_link_queue.add(link_url)
                except KeyError as e: # <a> tag without href
                    pass

            images = soup.find_all('img')
            self.repo_files[url]['images'] = len(images)

    def check_file_count(self):
        '''
        Checks if added files is equal to or greater than the input num_pages
        Displays the files if so and returns a False boolean to indicate that crawling should stop
        '''
        if self.file_count >= self.num_pages:
            self.display()
            return False
        return True

    def display(self):
        '''
        For jupyter notebook, displays a table of all files in repo
        '''
        html = '<table><tr><td>Live URL</td><td>File</td><td>Status</td><td># Links</td><td># Images</td></tr>'
        for key in self.repo_files:
            status = self.repo_files[key]['status']
            filename = self.repo_files[key]['filename']
            filename = f'repository/{filename}'
            links = self.repo_files[key]['links']
            images = self.repo_files[key]['images']
            html += f'<tr><td><a href={key}>{key}<td><a href={filename}>{key}</a></td><td>{status}</td><td>{links}</td><td>{images}</td></tr>'
        html += '</table>'
        display(HTML(html))









