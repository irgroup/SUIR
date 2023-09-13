
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

        if c > self.criterion_threshold:
            # print('Click!')
            return True
    
        # print('No click...')
        return False