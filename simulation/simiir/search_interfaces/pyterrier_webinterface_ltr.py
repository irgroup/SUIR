import pandas as pd
import requests 
import json
import glob

from simiir.search_interfaces import Document
from simiir.search_interfaces.base_interface import BaseSearchInterface

from ifind.search.response import Response

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Text, ARRAY
from simiir.search_contexts.search_context import SearchContext


from db_utils import WapoEntry, get_wapo_entry
from utils.interface_utils import LtrPreparator

from sklearn.ensemble import RandomForestRegressor

Base = declarative_base()

import pyterrier as pt
    
    
def fetch_and_parse(url):
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

class PyterrierWebSearchInterfaceLTR(BaseSearchInterface):
    """

    """
    def __init__(self):
        self._last_response = None
        self._last_query = None
        
        conn_string = 'postgresql://root@postgres:5432/' + "wapo"
        engine = create_engine(conn_string)
        Session = sessionmaker(bind=engine)
        self._session = Session()
        self._filter_seen_rel = False
        self._search_context = None

        if not pt.started():
            pt.init()

        self._indices_paths = [path for path in glob.glob("/workspace/indices/*") if "readme" not in path]
        index_ref = pt.IndexRef.of(self._indices_paths[0])
        index = pt.IndexFactory.of(index_ref)
        self._bm25 = pt.BatchRetrieve(index , wmodel='BM25', num_results=1000)


    def train_ltr_model(self, query, topic, rel_docs, nrel_docs):
        
        ltr_prep = LtrPreparator(self._indices_paths[0], query, topic)

        ltr_prep.add_rel_docs(rel_docs)
        ltr_prep.add_nrel_docs(nrel_docs)
        docs = rel_docs | nrel_docs

        ltr_prep.set_cnt_vectorizer(docs)
            
        rf = RandomForestRegressor(n_estimators=10)

        pipe = self._bm25 >> pt.apply.doc_features(lambda row: ltr_prep.vectorize_doc(row['docno'])) >> pt.ltr.apply_learned_model(rf)
        pipe.fit(ltr_prep.get_train_topics(), ltr_prep.get_current_qrels())

        return pipe
    
    def issue_query(self, query, num_results=100):
        """
        Allows one to issue a query to the underlying search engine. 
        """
        
        url = 'http://172.25.0.4:5000/results_wapo/'
        url_request = url + query.terms.decode('UTF-8').replace(":", "")
        _results = fetch_and_parse(url_request).get('response_query') 
        results = pd.DataFrame.from_dict(_results)
    
        #train ltr element

        #check whether there are enough training data
        
        rel_docs = set([str(doc.doc_id)[2:-1] for doc in self._search_context.get_relevant_documents()])
        nrel_docs = set([str(doc.doc_id)[2:-1] for doc in self._search_context.get_irrelevant_documents()])
        if len(rel_docs) >= 2 and len(nrel_docs) >= 2:
            #train ltr model
                
            pipe = self.train_ltr_model(query=self._last_query.terms.decode('UTF-8'), topic='1',rel_docs=rel_docs, nrel_docs=nrel_docs)
            results = pipe.search(self._last_query.terms.decode('UTF-8'))

        response = Response(query_terms=query.terms.decode('UTF-8'), query=query)
        
        for result in results.iterrows():
            
            #filter out seen relevant docs
            _docno = result[1].docno
            if self._filter_seen_rel and _docno in rel_docs:
                continue

            record = self._session.query(WapoEntry).filter_by(doc_id=_docno).first()

            if record:
                response.add_result(title=record.title,
                                    url=record.url,
                                    summary=record.kicker,
                                    docid=_docno,
                                    rank=result[1]['rank'] + 1,
                                    score=result[1].score,
                                    content=record.body,
                                    whooshid=_docno)
            
        response.result_total = len(results)
        
        self._last_query = query
        self._last_response = response
        
        return response
    
    def get_document(self, document_id):
        """
        Retrieves a Document object for the given document specified by parameter document_id.
        """
        
        record = self._session.query(WapoEntry).filter_by(doc_id=document_id.decode('utf-8')).first()
        title = record.title
        content = record.body
        document = Document(id=document_id, title=title, content=content, doc_id=document_id)
        
        return document

    def set_filter(self, filter, search_context : SearchContext):
        self._filter_seen_rel = filter
        self._search_context = search_context