
import abc
from simiir.text_classifiers.base_classifier import BaseTextClassifier

class SnippetClassifier(BaseTextClassifier):
    """
    TODO: add documentation.
    """
    def __init__(self, topic, search_context, criterion='title_tf', criterion_threshold=1, rprob=1.0, nprob=1.0, base_seed=0):
        """
        TODO: add documentation.
        """

        self.criterion = criterion
        self.criterion_threshold = criterion_threshold

        super(SnippetClassifier, self).__init__(topic, search_context)
        

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
