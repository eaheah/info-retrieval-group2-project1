from bs4 import BeautifulSoup
import os
import shutil
from random import random

def tags_below_index(lst, x):
    cur_x = 0
    count = 0
    while cur_x < x:
        count += lst[cur_x]
    return count

def tags_above_index(lst, x):
    cur_x = x + 1
    count = 0
    while cur_x < len(lst):
        count += lst[cur_x]
    return count

def non_tags_between_index(lst, i, j):
    cur_x = i + 1
    count = 0
    while cur_x < j:
        count += 1 - lst[cur_x]
    return count

def lst_score(lst, i, j):
    return tags_below_index(lst, i) + non_tags_between_index(lst, i, j) + tags_above_index(lst, j)

def neighbor(lst, i, j):
    # find randomized neighbor
    max_move_dist = round(len(lst) * .20)
    new_i += i + (2*max_move_dist*random()) - max_move_dist
    new_j += j + (2*max_move_dist*random()) - max_move_dist
    if new_i < 0:
        new_i = 0
    if new_j >= len(lst):
        new_j = len(lst) - 1
    if new_i >= new_j and new_j > 0:
        new_i = new_j - 1
    else:
        new_i = 0
        new_j = 1
    return new_i, new_j

class ContentProcessor:

    def process_repository(self, src_repo='repository'):
        self.src_repo = src_repo
        self.initialize_dst_repo()
        for file in os.listdir(self.src_repo):
            print(file)
            self.process_file(os.path.join(self.src_repo, file), file)

    def process_file(self, filename, fname):
        with open(filename, 'r') as f:
            # f = open(filename) # file never gets closed otherwise
            soup = BeautifulSoup(f, 'html.parser')
            #print(soup.body.prettify())
            bool_tag_list = self.clean_html(soup)
            with open (os.path.join('processed', fname), 'w') as f2:
                f2.write(bool_tag_list)
            # use simulated anealling to optimize indices

            #i, j = self.anneal(bool_tag_list)
            #main_content = self.extract_content(soup, bool_tag_list, i, j)

            # save content to (.txt?) file

    def clean_html(self, soup):
        ''' should return list of for optimization problem
            1 when tag is encountered and 0 for non tag
            some tags need to be ignored when they don't matter
        '''
        new_body = ""
        new_body += str(soup.title)
        #new_body.append("<body>")
        #for child in soup.body.children:
            #pass
        new_body += str(soup.body)

        return new_body

    def anneal(self, bool_tag_list):
        if len(bool_tag_list) <= 1:
            # maybe throw exception here
            return None, None
        i = round(random() * .5 * (len(bool_tag_list) - 1))
        j = round((1 - random() * .5) * (len(bool_tag_list) - 1))
        if i == j:
            i -= 1
        old_score = lst_score(bool_tag_list, i, j)
        T = 1.0
        T_min = 0.00001
        alpha = 0.9
        while T > T_min:
            it = 0
            while it < 50:
                new_i, new_j = neighbor(bool_tag_list, i, j)
                new_score = lst_score(bool_tag_list, new_i, new_j)
                ap = exp((old_score - new_score) / T)
                if ap > random():
                    i = new_i
                    j = new_j
                    old_cost = new_cost
                it += 1
            T = T * alpha
        return i, j

    def initialize_dst_repo(self):
        '''
        If repository exists from previous run, it is deleted
        Creates repository
        '''
        self.dst_repo = 'processed'
        if os.path.isdir(self.dst_repo):
            shutil.rmtree(self.dst_repo)
        os.mkdir(self.dst_repo)

    def extract_content(self, soup, bool_tag_list, i, j):
        pass
