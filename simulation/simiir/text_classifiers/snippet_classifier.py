
import abc
from simiir.text_classifiers.base_classifier import BaseTextClassifier

from simiir.query_generators.utils import IdfProvider, get_stopwords, filter_keywords

from simiir.search_contexts.search_context import SearchContext
from collections import Counter

import pickle


class SnippetClassifier(BaseTextClassifier):
    """
    TODO: add documentation.
    """
    def __init__(self, topic, search_context, criterion='title_tf', criterion_threshold=1, rprob=1.0, nprob=1.0, base_seed=0, corpus=None):
        """
        TODO: add documentation.
        """

        self.criterion = criterion
        self.criterion_threshold = criterion_threshold
        self._corpus = corpus
        self._index_path=f'/app/indices/{self._corpus}/data.properties'
        self._query_path = f"/workspace/data/{self._corpus}/title_queries"

        self._queries = self.get_queries(self._query_path)
        self._idf_provider = IdfProvider(self._index_path, get_stopwords())
        topic_path = f"/workspace/data/{self._corpus}/{self._corpus}_topics.pkl"
        self._topics = pickle.load(open(topic_path, "rb"))

        self.set_context_terms(search_context)

        super(SnippetClassifier, self).__init__(topic, search_context)
    
    def get_queries(self, query_file):
        queries = {}

        with open(query_file) as f:
            queries = {}
            for line in f.readlines():
                parts = line.split(',')
                queries[parts[2]] = parts[3].strip()

        return queries

    def set_context_terms(self, search_context : SearchContext):

        topic_id = search_context.topic.id
        topic_context = self._topics[self._topics['qid'] == topic_id]
        start_terms = self._queries[topic_id].split(" ")
        
        terms_description = set(topic_context['description'].values[0].split(" "))
        terms_narrative = set(topic_context['narrative'].values[0].split(" "))

        context_terms = terms_narrative.union(terms_description)
        context_terms = [term for term in context_terms if term not in start_terms]

        if True:
            #generate list of low signal terms from desription/narrative

            all_terms = []

            for _, row in self._topics.iterrows():
                all_terms += row['description'].split(" ")
                all_terms += row['narrative'].split(" ")

            cnt_list = Counter(all_terms)
            cnt_list = {k:v for k, v in sorted(cnt_list.items(), key=lambda item: -item[1])}
            
            context_terms = [term for term in context_terms if cnt_list[term] <= 3]

        context_terms = filter_keywords(self._idf_provider, context_terms)
        for term in context_terms:
            search_context.add_context_term(term)



    @abc.abstractmethod
    def is_relevant(self, document):
        """
        TODO: add documentation.
        """

        if self.criterion == 'title_tf':
            c = self._search_context._current_snippet.content.get('title_tf')

        if self.criterion == 'summary_tf':
            c = self._search_context._current_snippet.content.get('summary_tf')

        if self.criterion == 'title_bm25':
            c = self._search_context._current_snippet.content.get('title_bm25')

        if self.criterion == 'summary_bm25':
            c = self._search_context._current_snippet.content.get('summary_bm25')

        if self.criterion in ['topic_knowledge', 'full_knowledge']:

            if self.criterion == 'topic_knowledge':
                terms = set(self._search_context.get_context_terms())

            if self.criterion == 'full_knowledge':
                topic_terms = set(self._search_context.get_context_terms())
                rel_terms = set(self._search_context.get_rel_found_terms())
                terms = topic_terms.union(rel_terms)

            summary = self._search_context._current_snippet.content.get('summary')
            summary_terms = set(summary.split())
            term_overlap = summary_terms.intersection(terms)

            c = len(term_overlap)

        if c > self.criterion_threshold:
            
            # print('Click!')
            return True
    
        # print('No click...')
        return False
