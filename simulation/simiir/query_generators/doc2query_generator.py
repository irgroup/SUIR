from simiir.query_generators.base_generator import BaseQueryGenerator
import requests
import urllib.parse
from simiir.search_contexts.search_context import SearchContext
import requests
import json
import re
import pyterrier as pt
from .utils import IdfProvider, get_stopwords, filter_keywords

class Doc2QueryGenerator(BaseQueryGenerator):
    """
    A query generator that selects candidate queries based on doc2query queries from relevant docs
    """

    def __init__(self, stopword_file, query_file, user, background_file=[], index_path='/workspace/index_all_fields_new/data.properties', use_relevant=True, use_filter=True):
        super(Doc2QueryGenerator, self).__init__(stopword_file, background_file=background_file)
        self.__queries = self.get_queries(query_file)
        self.__user = user
        self.__use_relevant = use_relevant
        self.__idf_provider = IdfProvider(index_path, get_stopwords())
        self._user_filter = use_filter

    def get_queries(self, query_file):
        queries = {}

        with open(query_file) as f:
            queries = {}
            for line in f.readlines():
                parts = line.split(',')
                queries[parts[2]] = parts[3].strip()

        return queries
    
    def fetch_and_parse(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print ("Http Error:", errh)
            return
        except requests.exceptions.ConnectionError as errc:
            print ("Error Connecting:", errc)
            return
        except requests.exceptions.Timeout as errt:
            print ("Timeout Error:", errt)
            return
        except requests.exceptions.RequestException as err:
            print ("Something went wrong", err)
            return
        try:
            data = json.loads(response.text)
            return data
        except json.JSONDecodeError as e:
            print("Failed to decode:", e)
            return
        
    def get_new_canidate(self, candidate_terms, search_context: SearchContext):
        topic = search_context.topic.id
        start_q = self.__queries[topic]

        for candidate_term in candidate_terms:
            if not self._has_query_been_issued(search_context.get_issued_queries(), f"{start_q} {candidate_term}"):
                return f"{start_q} {candidate_term}"

        return
        
    def generate_query(self, search_context : SearchContext):
        
        candidate_terms = search_context.get_rel_found_terms()

        new_query = self.get_new_canidate(candidate_terms, search_context)
        
        if new_query:
            return new_query
        
        #calc new rel terms
        #TODO improve processing speed by avoiding unneccessary computations

        exam_snippetes_docs = set(search_context.get_all_examined_snippets())
        
        if self.__use_relevant:
            rel_docs = set(search_context.get_relevant_documents())
            non_rel_snippets = exam_snippetes_docs.difference(rel_docs)
        else:
            non_rel_snippets = exam_snippetes_docs

        non_rel_keywords = self.generate_keywords_from_docs(non_rel_snippets, search_context)

        search_context.add_nrel_found_terms(non_rel_keywords)

        candidate_terms = search_context.get_nrel_found_terms()
        new_query = self.get_new_canidate(candidate_terms, search_context)

        if new_query:
            return new_query
        else:
            print("This case should not have happened but it did, no new keywords could be extracted")
            return
            

    def generate_keywords_from_docs(self, docs, search_context : SearchContext):
        keywords = []
        used_docs = search_context.get_used_docs()

        for doc in docs:
            if not doc.doc_id in used_docs:
                docno = str(doc.doc_id)[2:-1].replace("/", "$")
                url = f"http://172.23.0.4:5000/doc2query/{docno}"

                for query_str in self.fetch_and_parse(url)['response_d2q']:
                    keywords += query_str.split(" ")

                search_context.add_used_doc(doc.doc_id)

        return filter_keywords(self.__idf_provider, keywords)
        
    def get_next_query(self, search_context : SearchContext):
        
        topic = search_context.topic.id
        #first query
        if not search_context.get_last_query():
            #not the most elegant way to access the search engine
            search_context.set_filter(self._user_filter)
            return self.__queries[topic]

        #add knowledge from past relevant docs
        if self.__use_relevant:
            keywords = self.generate_keywords_from_docs(search_context.get_relevant_documents(), search_context)
            search_context.add_rel_found_terms(keywords)


        return self.generate_query(search_context)

    