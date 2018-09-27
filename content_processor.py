from bs4 import BeautifulSoup
import os

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

class ContentProcessor:
    def process_repository(self, src_repo='repository'):
        self.src_repo = src_repo
        initialize_dst_repo()
        for file in os.listdir(self.src_repo):
            process_file(file)
    
    def process_file(self, filename):
        f = open(filename)
        soup = BeautifulSoup(f, 'html.parser')
        bool_tag_list = clean_html(soup)
        i, j = maximize_score(bool_tag_list)
        main_content = extract_content(soup, bool_tag_list, i, j)
        # save content to (.txt?) file
        
    def clean_html(self, soup):
        ''' should return list of for optimization problem 
            1 when tag is encountered and 0 for non tag    
            some tags need to be ignored when they don't matter '''
        
    def maximize_score(self, bool_tag_list):
        i = 0
        j = len(bool_tag_list) - 1
        if j == -1:
            # blank html maybe throw exception here
            return None, None
        score = 0
        rounds_since_score_improved = 0
        '''
        while true:
            cur_score = lst_score(bool_tag_list, i, j)
            if cur_score > score:
                score = cur_score
                rounds_since_score_improved = 0
            else if score stagnant:
                break
            move i and j
        '''
    
    def initialize_dst_repo(self):
        '''
        If repository exists from previous run, it is deleted
        Creates repository
        '''
        self.dst_repo = 'processed'
        if os.path.isdir(self.dst_repo):
            shutil.rmtree(self.dst_repo)
        os.mkdir(self.dst_repo)
        
        
    