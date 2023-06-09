import argparse
import linecache
import math
from collections import Counter

from english_indexer import *


# https://medium.com/analytics-vidhya/search-engine-in-python-from-scratch-c3f7cc453250
class FileTraverser():
    def __init__(self):
        pass

    def search_token(self, high, filename, inp_token):
        low = 0
        while low < high:
            mid = (low + high) // 2
            line = linecache.getline(filename, mid)
            token = line.split('-')[0]
            if inp_token == token:
                token_info = line.split('-')[1:-1]
                return token_info
            elif inp_token > token:
                low = mid + 1
            else:
                high = mid
        return None

    def search_title(self, page_id):
        title = linecache.getline('../wiki_index/id_title_map.txt', int(page_id) + 1).strip()
        title = title.split('-', 1)[1]
        return title

    def search_field_file(self, field, file_num, line_num):
        if line_num != '':
            line = linecache.getline(f'../wiki_index/{field}_data_{str(file_num)}.txt',
                                     int(line_num)).strip()
            postings = line.split('-')[1]
            return postings
        return ''

    def get_token_info(self, token):
        char_list = [chr(i) for i in range(97, 123)]
        num_list = [str(i) for i in range(0, 10)]
        if token[0] in char_list:
            with open(f'../wiki_index/tokens_info_{token[0]}_count.txt', 'r') as f:
                num_tokens = int(f.readline().strip())
            tokens_info_pointer = f'../wiki_index/tokens_info_{token[0]}.txt'
            token_info = self.search_token(num_tokens, tokens_info_pointer, token)
        elif token[0] in num_list:
            with open(f'../wiki_index/tokens_info_{token[0]}_count.txt', 'r') as f:
                num_tokens = int(f.readline().strip())
            tokens_info_pointer = f'../wiki_index/tokens_info_{token[0]}.txt'
            token_info = self.search_token(num_tokens, tokens_info_pointer, token)
        else:
            with open(f'../wiki_index/tokens_info_others_count.txt', 'r') as f:
                num_tokens = int(f.readline().strip())
            tokens_info_pointer = f'../wiki_index/tokens_info_others.txt'
            token_info = self.search_token(num_tokens, tokens_info_pointer, token)
        return token_info


class Ranker:
    def __init__(self, num_pages):
        self.num_pages = num_pages

    def do_ranking(self, page_freq, page_postings):
        result = defaultdict(float)
        weightage_dict = {'title': 1.0, 'body': 0.6, 'category': 0.4, 'infobox': 0.75, 'link': 0.20, 'reference': 0.25}
        for token, field_post_dict in page_postings.items():
            for field, postings in field_post_dict.items():
                weightage = weightage_dict[field]
                if len(postings) > 0:
                    for post in postings.split(';'):
                        id, post = post.split(':')
                        result[id] += weightage * (1 + math.log(int(post))) * math.log(
                            (self.num_pages - int(page_freq[token])) / int(page_freq[token]))
        return result


class QueryResults:
    def __init__(self, file_traverser):
        self.file_traverser = file_traverser

    def simple_query(self, preprocessed_query):
        page_freq, page_postings = {}, defaultdict(dict)
        for token in preprocessed_query:
            token_info = self.file_traverser.get_token_info(token)
            if token_info:
                file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
                line_map = {
                    'title': title_line, 'body': body_line, 'category': category_line, 'infobox': infobox_line,
                    'link': link_line, 'reference': reference_line
                }
                for field_name, line_num in line_map.items():
                    if line_num != '':
                        posting = self.file_traverser.search_field_file(field_name, file_num, line_num)
                        page_freq[token] = len(posting.split(';'))
                        page_postings[token][field_name] = posting
        return page_freq, page_postings

    def field_query(self, preprocessed_query):
        page_freq, page_postings = {}, defaultdict(dict)
        for field, token in preprocessed_query:
            token_info = self.file_traverser.get_token_info(token)
            if token_info:
                file_num, freq, title_line, body_line, category_line, infobox_line, link_line, reference_line = token_info
                line_map = {
                    'title': title_line, 'body': body_line, 'category': category_line, 'infobox': infobox_line,
                    'link': link_line, 'reference': reference_line
                }
                field_map = {
                    't': 'title', 'b': 'body', 'c': 'category', 'i': 'infobox', 'l': 'link', 'r': 'reference'
                }
                field_name = field_map[field]
                line_num = line_map[field_name]
                posting = self.file_traverser.search_field_file(field_name, file_num, line_num)
                page_freq[token] = len(posting)
                page_postings[token][field_name] = posting
        return page_freq, page_postings


class RunQuery:
    def __init__(self, text_pre_processor, file_traverser, ranker, query_results):
        self.file_traverser = file_traverser
        self.text_pre_processor = text_pre_processor
        self.ranker = ranker
        self.query_results = query_results

    def identify_query_type(self, query):
        field_replace_map = {
            ' t:': ';t:',
            ' b:': ';b:',
            ' c:': ';c:',
            ' i:': ';i:',
            ' l:': ';l:',
            ' r:': ';r:',
        }
        if (
                't:' in query or 'b:' in query or 'c:' in query or 'i:' in query or 'l:' in query or 'r:' in query) and query[
                                                                                                                        0:2] not in [
            't:', 'b:', 'i:', 'c:', 'r:', 'l:']:
            for k, v in field_replace_map.items():
                if k in query:
                    query = query.replace(k, v)
            query = query.lstrip(';')
            return query.split(';')[0], query.split(';')[1:]
        elif 't:' in query or 'b:' in query or 'c:' in query or 'i:' in query or 'l:' in query or 'r:' in query:
            for k, v in field_replace_map.items():
                if k in query:
                    query = query.replace(k, v)
            query = query.lstrip(';')
            return query.split(';'), None
        else:
            return query, None

    def return_query_results(self, query, query_type):
        if query_type == 'field':
            preprocessed_query = [[qry.split(':')[0], self.text_pre_processor.preprocess_text(qry.split(':')[1])] for
                                  qry in query]
        else:
            preprocessed_query = self.text_pre_processor.preprocess_text(query)
        if query_type == 'field':
            preprocessed_query_final = []
            for field, words in preprocessed_query:
                for word in words:
                    preprocessed_query_final.append([field, word])
            page_freq, page_postings = self.query_results.field_query(preprocessed_query_final)
        else:
            page_freq, page_postings = self.query_results.simple_query(preprocessed_query)
        ranked_results = self.ranker.do_ranking(page_freq, page_postings)
        return ranked_results

    def take_input_from_file(self, file_name, num_results):
        results_file = file_name.split('.txt')[0]
        with open(file_name, 'r') as f:
            fp = open(results_file + '_op.txt', 'w')
            for i, query in enumerate(f):
                s = time.time()
                query = query.strip()
                query1, query2 = self.identify_query_type(query)
                if query2:
                    ranked_results1 = self.return_query_results(query1, 'simple')
                    ranked_results2 = self.return_query_results(query2, 'field')
                    ranked_results = Counter(ranked_results1) + Counter(ranked_results2)
                    results = sorted(ranked_results.items(), key=lambda item: item[1], reverse=True)
                    results = results[:num_results]
                    if results:
                        for id, _ in results:
                            title = self.file_traverser.search_title(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching document found')
                        fp.write('\n')
                elif type(query1) == type([]):
                    ranked_results = self.return_query_results(query1, 'field')
                    results = sorted(ranked_results.items(), key=lambda item: item[1], reverse=True)
                    results = results[:num_results]
                    if results:
                        for id, _ in results:
                            title = self.file_traverser.search_title(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching document found')
                        fp.write('\n')
                else:
                    ranked_results = self.return_query_results(query1, 'simple')
                    results = sorted(ranked_results.items(), key=lambda item: item[1], reverse=True)
                    results = results[:num_results]
                    if results:
                        for id, _ in results:
                            title = self.file_traverser.search_title(id)
                            fp.write(id + ', ' + title)
                            fp.write('\n')
                    else:
                        fp.write('No matching document found')
                        fp.write('\n')
                e = time.time()
                fp.write('Finished in ' + str(e - s) + ' seconds')
                fp.write('\n\n')
                print('Done query', i + 1)
            fp.close()
        print('Done writing results')

    def take_input_from_user(self, num_results):
        start = time.time()
        while True:
            query = input('Enter Query:- ')
            s = time.time()
            query = query.strip()
            query1, query2 = self.identify_query_type(query)
            if query2:
                ranked_results1 = self.return_query_results(query1, 'simple')
                ranked_results2 = self.return_query_results(query2, 'field')
                ranked_results = Counter(ranked_results1) + Counter(ranked_results2)
                results = sorted(ranked_results.items(), key=lambda item: item[1], reverse=True)
                results = results[:num_results]
                for id, _ in results:
                    title = self.file_traverser.search_title(id)
                    print(id + ',', title)
            elif type(query1) == type([]):
                ranked_results = self.return_query_results(query1, 'field')
                results = sorted(ranked_results.items(), key=lambda item: item[1], reverse=True)
                results = results[:num_results]
                for id, _ in results:
                    title = self.file_traverser.search_title(id)
                    print(id + ',', title)
            else:
                ranked_results = self.return_query_results(query1, 'simple')
                results = sorted(ranked_results.items(), key=lambda item: item[1], reverse=True)
                results = results[:num_results]
                for id, _ in results:
                    title = self.file_traverser.search_title(id)
                    print(id + ',', title)
            e = time.time()
            print('Finished in', e - s, 'seconds')
            print()


if __name__ == '__main__':
    start = time.time()
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--filename', action='store', type=str)
    arg_parser.add_argument('--num_results', action='store', default=10, type=int)
    args = arg_parser.parse_args()
    file_name = args.filename
    num_results = args.num_results
    print('Loading search engine...')
    stop_words = (set(stopwords.words("english")))
    html_tags = re.compile('&amp;|&apos;|&gt;|&lt;|&nbsp;|&quot;')
    stemmer = Stemmer('english')
    with open('../wiki_index/num_pages.txt', 'r') as f:
        num_pages = float(f.readline().strip())
    text_pre_processor = TextPreProcessor(html_tags, stemmer, stop_words)
    file_traverser = FileTraverser()
    ranker = Ranker(num_pages)
    query_results = QueryResults(file_traverser)
    run_query = RunQuery(text_pre_processor, file_traverser, ranker, query_results)
    temp = linecache.getline('../wiki_index/id_title_map.txt', 0)
    print('Loaded in', time.time() - start, 'seconds')
    print('Starting Querying')
    start = time.time()
    if file_name is not None:
        run_query.take_input_from_file(file_name, num_results)
    else:
        run_query.take_input_from_user(num_results)
    print('Done querying in', time.time() - start, 'seconds')
