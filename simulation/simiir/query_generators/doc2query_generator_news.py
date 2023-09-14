from simiir.query_generators.base_generator import BaseQueryGenerator
import requests
import urllib.parse
from simiir.search_contexts.search_context import SearchContext
import requests
import json
import re
import pyterrier as pt
from .utils import IdfProvider, get_stopwords, filter_keywords
import pickle

from collections import Counter


class Doc2QueryGeneratorNews(BaseQueryGenerator):
    """
    A query generator that selects candidate queries based on doc2query queries from seen relevant or all seen docs
    """

    def __init__(self, stopword_file, query_file, user, background_file=[], use_relevant=True, use_filter=True, use_topic_context=False, filter_low_signal_terms=True, corpus="dummy", low_signal_threshold = 3):
        super(Doc2QueryGeneratorNews, self).__init__(stopword_file, background_file=background_file)
        self.__corpus = corpus
        self.__index_path=f'/app/indices/{self.__corpus}/data.properties'
        
        self.__queries = self.get_queries(query_file)
        self.__user = user
        self.__use_relevant = use_relevant
        self.__use_topic_context = use_topic_context
        self._filter_low_signal_terms = filter_low_signal_terms
        self._low_signal_threshold = low_signal_threshold

        self.__idf_provider = IdfProvider(self.__index_path, get_stopwords())
        self._user_filter = use_filter

        self._topics = None

        if use_topic_context:
            topic_path = f"/workspace/data/{self.__corpus}/{self.__corpus}_topics.pkl"
            self._topics = pickle.load(open(topic_path, "rb"))

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
        
        #first try to use context terms
        if self.__use_topic_context:
            candidate_terms = search_context.get_context_terms()
            new_query = self.get_new_canidate(candidate_terms, search_context)
            if new_query:
                return new_query


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
                url = f"http://127.0.0.1:5001/doc2query_{self.__corpus}/{docno}"

                for query_str in self.fetch_and_parse(url)[f'response_d2q_{self.__corpus}']:
                    keywords += query_str.split(" ")

                search_context.add_used_doc(doc.doc_id)

        return filter_keywords(self.__idf_provider, keywords)
        
    def set_context_terms(self, search_context : SearchContext):

        topic_id = search_context.topic.id
        topic_context = self._topics[self._topics['qid'] == topic_id]
        start_terms = self.__queries[topic_id].split(" ")
        
        terms_description = set(topic_context['description'].values[0].split(" "))
        terms_narrative = set(topic_context['narrative'].values[0].split(" "))

        context_terms = terms_narrative.union(terms_description)
        context_terms = [term for term in context_terms if term not in start_terms]

        if self._filter_low_signal_terms:
            #generate list of low signal terms from desription/narrative

            all_terms = []

            for _, row in self._topics.iterrows():
                all_terms += row['description'].split(" ")
                all_terms += row['narrative'].split(" ")

            cnt_list = Counter(all_terms)
            cnt_list = {k:v for k, v in sorted(cnt_list.items(), key=lambda item: -item[1])}
            
            context_terms = [term for term in context_terms if cnt_list[term] <= self._low_signal_threshold]

        context_terms = filter_keywords(self.__idf_provider, context_terms)
        for term in context_terms:
            search_context.add_context_term(term)


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

        #add keywords from topic context (description and narrative)
        if self.__use_topic_context and not search_context.get_context_terms():
            self.set_context_terms(search_context)

        return self.generate_query(search_context)

    