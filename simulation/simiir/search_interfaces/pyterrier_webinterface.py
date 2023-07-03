import pandas as pd
import requests 
import json

from simiir.search_interfaces import Document
from simiir.search_interfaces.base_interface import BaseSearchInterface

from ifind.search.response import Response

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Text, ARRAY
from simiir.search_contexts.search_context import SearchContext

from db_utils import WapoEntry, get_wapo_entry

Base = declarative_base()
    
    
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

class PyterrierWebSearchInterface(BaseSearchInterface):
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
    
    def issue_query(self, query, num_results=100):
        """
        Allows one to issue a query to the underlying search engine. 
        """
        
        url = 'http://172.25.0.4:5000/results_wapo/'
        url_request = url + query.terms.decode('UTF-8').replace(":", "")
        _results = fetch_and_parse(url_request).get('response_query') 
        results = pd.DataFrame.from_dict(_results)
 
        response = Response(query_terms=query.terms.decode('UTF-8'), query=query)
        
        for result in results.iterrows():
            
            #filter out seen relevant docs
            _docno = result[1].docno
            if self._filter_seen_rel:

                rel_docs = set([str(doc.doc_id)[2:-1] for doc in self._search_context.get_relevant_documents()])
                if _docno in rel_docs:
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