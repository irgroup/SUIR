from simiir.query_generators import utils
from db_utils import gen_session, get_wapo_entry, get_wapo_doc2query
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np
import pandas as pd


class LtrPreparator:

    def __init__(self, index_path, query, topic) -> None:
        self.idf_provider = utils.IdfProvider(index_path, utils.get_stopwords())
        self.session = gen_session()
        self.rel_docs = set()
        self.nrel_docs = set()
        self.query = query
        self.topic = topic

    def add_rel_docs(self, docs):
        self.rel_docs |= set(docs)

    def add_nrel_docs(self, docs):
        self.nrel_docs |= set(docs)

    def get_rel_docs(self):
        return self.rel_docs

    def get_nrel_docs(self):
        return self.nrel_docs

    def featurize_doc(self, doc_id, idf_provider):
        queries = get_wapo_doc2query(self.session, doc_id).querygen
        all_queries = " ".join(queries).split(" ")
        keywords = " ".join(utils.filter_keywords(idf_provider, all_queries))

        return keywords

    def vectorize_doc(self, doc):
        doc = self.featurize_doc(doc, self.idf_provider)
        return self.cnt_vect.transform([doc]).toarray()[0]

    def gen_local_corpus(self, docs):
        texts = [self.featurize_doc(doc, self.idf_provider) for doc in docs]
        return texts
    
    def set_cnt_vectorizer(self, docs):
        #check wether docs are texts
        if len(list(docs)[0].split(" ")) <= 1:
            docs = self.gen_local_corpus(docs)
            
        self.cnt_vect = CountVectorizer().fit(docs)

    def get_train_topics(self):
        t = np.array([[int(self.topic), self.query]])
        topics = pd.DataFrame(data=t, columns=['qid', 'query'])
        #topics = topics.astype({'qid' : 'object'})
        return topics

    def get_current_qrels(self):
        
        rel_qrels = [[int(self.topic), docno, 1] for docno in self.rel_docs]
        nrel_qrels = [[int(self.topic), docno, 0] for docno in self.nrel_docs]
        qrels = pd.DataFrame(data=np.array(rel_qrels+nrel_qrels), columns=['qid', 'docno',	'label'])
        qrels = qrels.astype({'label': 'int64'})
        
        return qrels
