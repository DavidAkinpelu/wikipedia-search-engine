import os
import re
import sys
import time
import xml.sax
from bz2 import BZ2File
from collections import defaultdict

from Stemmer import Stemmer
from nltk.corpus import stopwords
from tqdm import tqdm

index_map = defaultdict(str)
num_files = 0
num_pages = 0
id_title_map = {}


# https://medium.com/analytics-vidhya/search-engine-in-python-from-scratch-c3f7cc453250
class TextPreProcessor:
    def __init__(self, html_tags, stemmer, stop_words):
        self.html_tags = html_tags
        self.stemmer = stemmer
        self.stop_words = stop_words

    def remove_stopwords(self, text_data):
        cleaned_text = [word for word in text_data if word not in self.stop_words]
        return cleaned_text

    def stem_text(self, text_data):
        cleaned_text = self.stemmer.stemWords(text_data)
        return cleaned_text

    def remove_non_ascii(self, text_data):
        cleaned_text = ''.join([i if ord(i) < 128 else ' ' for i in text_data])
        return cleaned_text

    def remove_html_tags(self, text_data):
        cleaned_text = re.sub(self.html_tags, ' ', text_data)
        return cleaned_text

    def remove_special_chars(self, text_data):
        cleaned_text = ''.join(ch if ch.isalnum() else ' ' for ch in text_data)
        return cleaned_text

    def remove_keywords(self, text_data):
        text_data = text_data.replace('\n', ' ').replace('File:', ' ')
        text_data = re.sub('(http://[^ ]+)', ' ', text_data)
        text_data = re.sub('(https://[^ ]+)', ' ', text_data)
        return text_data

    def tokenize_sentence(self, text_data, flag=False):
        if flag:
            text_data = self.remove_keywords(text_data)
            text_data = re.sub('\{.*?\}|\[.*?\]|\=\=.*?\=\=', ' ', text_data)
        cleaned_text = self.remove_non_ascii(text_data)
        cleaned_text = self.remove_html_tags(cleaned_text)
        cleaned_text = self.remove_special_chars(cleaned_text)
        return cleaned_text.split()

    def preprocess_text(self, text_data, flag=False):
        cleaned_data = self.tokenize_sentence(text_data.lower(), flag)
        cleaned_data = self.remove_stopwords(cleaned_data)
        cleaned_data = self.stem_text(cleaned_data)
        return cleaned_data


class PageProcessor:
    def __init__(self, text_pre_processor):
        self.text_pre_processor = text_pre_processor

    def process_title(self, title):
        cleaned_title = self.text_pre_processor.preprocess_text(title)
        return cleaned_title

    def process_infobox(self, text):
        cleaned_infobox = []
        try:
            text = text.split('\n')
            i = 0
            while '{{Infobox' not in text[i]:
                i += 1
            data = []
            data.append(text[i].replace('{{Infobox', ' '))
            i += 1
            while text[i] != '}}':
                if '{{Infobox' in text[i]:
                    dt = text[i].replace('{{Infobox', ' ')
                    data.append(dt)
                else:
                    data.append(text[i])
                i += 1
            infobox_data = ' '.join(data)
            cleaned_infobox = self.text_pre_processor.preprocess_text(infobox_data)
        except:
            pass
        return cleaned_infobox

    def process_text_body(self, text):
        cleaned_text_body = text_pre_processor.preprocess_text(text, True)
        return cleaned_text_body

    def process_category(self, text):
        cleaned_category = []
        try:
            text = text.split('\n')
            i = 0
            while not text[i].startswith('[[Category:'):
                i += 1
            data = []
            data.append(text[i].replace('[[Category:', ' ').replace(']]', ' '))
            i += 1
            while text[i].endswith(']]'):
                dt = text[i].replace('[[Category:', ' ').replace(']]', ' ')
                data.append(dt)
                i += 1
            category_data = ' '.join(data)
            cleaned_category = self.text_pre_processor.preprocess_text(category_data)
        except:
            pass
        return cleaned_category

    def process_links(self, text):
        cleaned_links = []
        try:
            links = ''
            text = text.split("==External links==")
            if len(text) > 1:
                text = text[1].split("\n")[1:]
                for txt in text:
                    if txt == '':
                        break
                    if txt[0] == '*':
                        text_split = txt.split(' ')
                        link = [wd for wd in text_split if 'http' not in wd]
                        link = ' '.join(link)
                        links += ' ' + link
            cleaned_links = self.text_pre_processor.preprocess_text(links)
        except:
            pass
        return cleaned_links

    def process_references(self, text):
        cleaned_references = []
        try:
            references = ''
            text = text.split('==References==')
            if len(text) > 1:
                text = text[1].split("\n")[1:]
                for txt in text:
                    if txt == '':
                        break
                    if txt[0] == '*':
                        text_split = txt.split(' ')
                        reference = [wd for wd in text_split if 'http' not in wd]
                        reference = ' '.join(reference)
                        references += ' ' + reference
            cleaned_references = self.text_pre_processor.preprocess_text(references)
        except:
            pass
        return cleaned_references

    def process_page(self, title, text):
        title = self.process_title(title)
        body = self.process_text_body(text)
        category = self.process_category(text)
        infobox = self.process_infobox(text)
        link = self.process_links(text)
        reference = self.process_references(text)
        return title, body, category, infobox, link, reference


class WriteData():
    def __init__(self):
        pass

    def write_id_title_map(self):
        global id_title_map
        temp_id_title = []
        temp_id_title_map = sorted(id_title_map.items(), key=lambda item: int(item[0]))
        for id, title in tqdm(temp_id_title_map):
            t = str(id) + '-' + title.strip()
            temp_id_title.append(t)
        with open('../wiki_index/id_title_map.txt', 'a', encoding="utf-8") as f:
            f.write('\n'.join(temp_id_title))
            f.write('\n')

    def write_intermed_index(self):
        global num_files
        global index_map
        temp_index_map = sorted(index_map.items(), key=lambda item: item[0])
        temp_index = []
        for word, posting in tqdm(temp_index_map):
            temp_index.append(word + '-' + posting)
        with open(f'../wiki_index/index_{num_files}.txt', 'w', encoding="utf-8") as f:
            f.write('\n'.join(temp_index))
        num_files += 1

    def write_final_files(self, data_to_merge, num_files_final):
        title_dict, body_dict, category_dict, infobox_dict, link_dict, reference_dict = defaultdict(dict), defaultdict(
            dict), defaultdict(dict), defaultdict(dict), defaultdict(dict), defaultdict(dict)
        unique_tokens_info = {}
        sorted_data = sorted(data_to_merge.items(), key=lambda item: item[0])
        for i, (token, postings) in tqdm(enumerate(sorted_data)):
            for posting in postings.split(';')[:-1]:
                id = posting.split(':')[0]
                fields = posting.split(':')[1]
                if 't' in fields:
                    title_dict[token][id] = re.search(r'.*t([0-9]*).*', fields).group(1)
                if 'b' in fields:
                    body_dict[token][id] = re.search(r'.*b([0-9]*).*', fields).group(1)
                if 'c' in fields:
                    category_dict[token][id] = re.search(r'.*c([0-9]*).*', fields).group(1)
                if 'i' in fields:
                    infobox_dict[token][id] = re.search(r'.*i([0-9]*).*', fields).group(1)
                if 'l' in fields:
                    link_dict[token][id] = re.search(r'.*l([0-9]*).*', fields).group(1)
                if 'r' in fields:
                    reference_dict[token][id] = re.search(r'.*r([0-9]*).*', fields).group(1)
            token_info = '-'.join([token, str(num_files_final), str(len(postings.split(';')[:-1]))])
            unique_tokens_info[token] = token_info + '-'
        final_titles, final_body_texts, final_categories, final_infoboxes, final_links, final_references = [], [], [], [], [], []
        for i, (token, _) in tqdm(enumerate(sorted_data)):
            if token in title_dict.keys():
                posting = title_dict[token]
                final_titles = self.get_diff_postings(token, posting, final_titles)
                t = len(final_titles)
                unique_tokens_info[token] += str(t) + '-'
            else:
                unique_tokens_info[token] += '-'
            if token in body_dict.keys():
                posting = body_dict[token]
                final_body_texts = self.get_diff_postings(token, posting, final_body_texts)
                t = len(final_body_texts)
                unique_tokens_info[token] += str(t) + '-'
            else:
                unique_tokens_info[token] += '-'
            if token in category_dict.keys():
                posting = category_dict[token]
                final_categories = self.get_diff_postings(token, posting, final_categories)
                t = len(final_categories)
                unique_tokens_info[token] += str(t) + '-'
            else:
                unique_tokens_info[token] += '-'
            if token in infobox_dict.keys():
                posting = infobox_dict[token]
                final_infoboxes = self.get_diff_postings(token, posting, final_infoboxes)
                t = len(final_infoboxes)
                unique_tokens_info[token] += str(t) + '-'
            else:
                unique_tokens_info[token] += '-'
            if token in link_dict.keys():
                posting = link_dict[token]
                final_links = self.get_diff_postings(token, posting, final_links)
                t = len(final_links)
                unique_tokens_info[token] += str(t) + '-'
            else:
                unique_tokens_info[token] += '-'
            if token in reference_dict.keys():
                posting = reference_dict[token]
                final_references = self.get_diff_postings(token, posting, final_references)
                t = len(final_references)
                unique_tokens_info[token] += str(t) + '-'
            else:
                unique_tokens_info[token] += '-'
        with open('../wiki_index/tokens_info.txt', 'a', encoding="utf-8") as f:
            f.write('\n'.join(unique_tokens_info.values()))
            f.write('\n')
        self.write_diff_postings('title', final_titles, num_files_final)
        self.write_diff_postings('body', final_body_texts, num_files_final)
        self.write_diff_postings('category', final_categories, num_files_final)
        self.write_diff_postings('infobox', final_infoboxes, num_files_final)
        self.write_diff_postings('link', final_links, num_files_final)
        self.write_diff_postings('reference', final_references, num_files_final)
        num_files_final += 1
        return num_files_final

    def get_diff_postings(self, token, postings, final_tag):
        postings = sorted(postings.items(), key=lambda item: int(item[0]))
        final_posting = token + '-'
        for id, freq in postings:
            final_posting += str(id) + ':' + freq + ';'
        final_tag.append(final_posting.rstrip(';'))
        return final_tag

    def write_diff_postings(self, tag_type, final_tag, num_files_final):
        with open(f'../wiki_index/{tag_type}_data_{str(num_files_final)}.txt', 'w',
                  encoding="utf-8") as f:
            f.write('\n'.join(final_tag))


class CreateIndex():
    def __init__(self, write_data):
        self.write_data = write_data

    def index(self, title, body, category, infobox, link, reference):
        global num_pages
        global index_map
        global id_title_map
        words_set, title_dict, body_dict, category_dict, infobox_dict, link_dict, reference_dict = set(), defaultdict(
            int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
        words_set.update(title)
        for word in title:
            title_dict[word] += 1
        words_set.update(body)
        for word in body:
            body_dict[word] += 1
        words_set.update(category)
        for word in category:
            category_dict[word] += 1
        words_set.update(infobox)
        for word in infobox:
            infobox_dict[word] += 1
        words_set.update(link)
        for word in link:
            link_dict[word] += 1
        words_set.update(reference)
        for word in reference:
            reference_dict[word] += 1
        for word in words_set:
            temp = re.sub(r'^((.)(?!\2\2\2))+$', r'\1', word)
            is_rep = len(temp) == len(word)
            if not is_rep:
                posting = str(num_pages) + ':'
                if title_dict[word]:
                    posting += 't' + str(title_dict[word])
                if body_dict[word]:
                    posting += 'b' + str(body_dict[word])
                if category_dict[word]:
                    posting += 'c' + str(category_dict[word])
                if infobox_dict[word]:
                    posting += 'i' + str(infobox_dict[word])
                if link_dict[word]:
                    posting += 'l' + str(link_dict[word])
                if reference_dict[word]:
                    posting += 'r' + str(reference_dict[word])
                posting += ';'
                index_map[word] += posting
        num_pages += 1
        if not num_pages % 40000:
            self.write_data.write_intermed_index()
            self.write_data.write_id_title_map()
            index_map = defaultdict(str)
            id_title_map = {}


class XMLParser(xml.sax.ContentHandler):
    def __init__(self, page_processor, create_index):
        self.tag = ''
        self.title = ''
        self.text = ''
        self.page_processor = page_processor
        self.create_index = create_index

    def startElement(self, name, attrs):
        self.tag = name

    def endElement(self, name):
        if name == 'page':
            if num_pages % 100 == 0:
                print(num_pages)
            id_title_map[num_pages] = self.title.lower()
            title, body, category, infobox, link, reference = self.page_processor.process_page(self.title, self.text)
            self.create_index.index(title, body, category, infobox, link, reference)
            self.tag = ""
            self.title = ""
            self.text = ""

    def characters(self, content):
        if self.tag == 'title':
            self.title += content
        if self.tag == 'text':
            self.text += content


class MergeFiles():
    def __init__(self, num_itermed_files, write_data):
        self.num_itermed_files = num_itermed_files
        self.write_data = write_data

    def merge_files(self):
        files_data = {}
        line = {}
        postings = {}
        is_file_empty = {i: 1 for i in range(self.num_itermed_files)}
        tokens = []
        i = 0
        while i < self.num_itermed_files:
            files_data[i] = open(f'../wiki_index/index_{i}.txt', 'r', encoding="utf-8")
            line[i] = files_data[i].readline().strip('\n')
            postings[i] = line[i].split('-')
            is_file_empty[i] = 0
            new_token = postings[i][0]
            if new_token not in tokens:
                tokens.append(new_token)
            i += 1
        tokens.sort(reverse=True)
        num_processed_postings = 0
        data_to_merge = defaultdict(str)
        num_files_final = 0
        while sum(is_file_empty.values()) != self.num_itermed_files:
            token = tokens.pop()
            num_processed_postings += 1
            if num_processed_postings % 30000 == 0:
                num_files_final = self.write_data.write_final_files(data_to_merge, num_files_final)
                data_to_merge = defaultdict(str)
            i = 0
            while i < self.num_itermed_files:
                if is_file_empty[i] == 0:
                    if token == postings[i][0]:
                        line[i] = files_data[i].readline().strip('\n')
                        data_to_merge[token] += postings[i][1]
                        if len(line[i]):
                            postings[i] = line[i].split('-')
                            new_token = postings[i][0]
                            if new_token not in tokens:
                                tokens.append(new_token)
                                tokens.sort(reverse=True)
                        else:
                            is_file_empty[i] = 1
                            files_data[i].close()
                            print(f'Removing file {str(i)}')
                            os.remove(f'../wiki_index/index_{str(i)}.txt')
                i += 1
        num_files_final = self.write_data.write_final_files(data_to_merge, num_files_final)
        return num_files_final


if __name__ == '__main__':
    start = time.time()
    html_tags = re.compile('&amp;|&apos;|&gt;|&lt;|&nbsp;|&quot;')
    stemmer = Stemmer('english')
    stop_words = (set(stopwords.words("english")))
    text_pre_processor = TextPreProcessor(html_tags, stemmer, stop_words)
    page_processor = PageProcessor(text_pre_processor)
    write_data = WriteData()
    create_index = CreateIndex(write_data)
    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, False)
    xml_parser = XMLParser(page_processor, create_index)
    parser.setContentHandler(xml_parser)
    # modified to parse bz2 multistream filed
    os.makedirs('../wiki_index/', exist_ok=True)
    print('parsing')
    parser.parse(BZ2File(sys.argv[1]))
    print('done parsing?')
    write_data.write_intermed_index()
    write_data.write_id_title_map()
    merge_files = MergeFiles(num_files, write_data)
    num_files_final = merge_files.merge_files()
    with open('../wiki_index/num_pages.txt', 'w', encoding="utf-8") as f:
        f.write(str(num_pages))
    num_tokens_final = 0
    with open('../wiki_index/tokens_info.txt', 'r', encoding="utf-8") as f:
        for line in f:
            num_tokens_final += 1
    with open('../wiki_index/num_tokens.txt', 'w', encoding="utf-8") as f:
        f.write(str(num_tokens_final))
    char_list = [chr(i) for i in range(97, 123)]
    num_list = [str(i) for i in range(0, 10)]
    with open(f'../wiki_index/tokens_info.txt', 'r', encoding="utf-8") as f:
        for line in tqdm(f):
            if line[0] in char_list:
                with open(f'../wiki_index/tokens_info_{line[0]}.txt', 'a', encoding="utf-8") as t:
                    t.write(line.strip())
                    t.write('\n')
            elif line[0] in num_list:
                with open(f'../wiki_index/tokens_info_{line[0]}.txt', 'a', encoding="utf-8") as t:
                    t.write(line.strip())
                    t.write('\n')
            else:
                with open(f'../wiki_index/tokens_info_others.txt', 'a', encoding="utf-8") as t:
                    t.write(line.strip())
                    t.write('\n')
    for ch in tqdm(char_list):
        tok_count = 0
        with open(f'../wiki_index/tokens_info_{ch}.txt', 'r', encoding="utf-8") as f:
            for line in f:
                tok_count += 1
        with open(f'../wiki_index/tokens_info_{ch}_count.txt', 'w', encoding="utf-8") as f:
            f.write(str(tok_count))
    for num in tqdm(num_list):
        tok_count = 0
        with open(f'../wiki_index/tokens_info_{num}.txt', 'r', encoding="utf-8") as f:
            for line in f:
                tok_count += 1
        with open(f'../wiki_index/tokens_info_{num}_count.txt', 'w', encoding="utf-8") as f:
            f.write(str(tok_count))
    try:
        tok_count = 0
        with open('../wiki_index/tokens_info_others.txt', 'r', encoding="utf-8") as f:
            tok_count += 1
        with open(f'../wiki_index/tokens_info_others_count.txt', 'w', encoding="utf-8") as f:
            f.write(str(tok_count))
    except:
        pass
    os.remove('../wiki_index/tokens_info.txt')
    print('Total tokens', num_tokens_final)
    print('Final files', num_files_final)
    end = time.time()
    print('Finished in -', end - start)
