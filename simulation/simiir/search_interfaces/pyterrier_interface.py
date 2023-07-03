import os
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-11-openjdk-amd64"

import pyterrier as pt
if not pt.started():
  pt.init()

from simiir.search_interfaces import Document
from simiir.search_interfaces.base_interface import BaseSearchInterface

from ifind.search.response import Response

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Text, ARRAY

Base = declarative_base()

class Table(Base):
    __tablename__ = 'webtables'
    docno = Column(String, primary_key=True)
    table_content = Column(Text)
    textBefore = Column(Text)
    textAfter = Column(Text)
    pageTitle = Column(String)
    title = Column(String)
    entities = Column(Text)
    url = Column(String)
    orientation = Column(String)
    header = Column(String)
    key_col = Column(String)
    relation = Column(ARRAY(String, dimensions=2))
    
    def __repr__(self):
        repr_str = f"docno={self.docno}, table_content={self.table_content}, textBefore={self.textBefore}, textAfter={self.textAfter},"\
        f"pageTitle={self.pageTitle}, title={self.title}, entities={self.entities}, url={self.url}, orientation={self.orientation},"\
        f"header={self.header}, key_col={self.key_col}"
        
        return repr_str

class PyterrierSearchInterface(BaseSearchInterface):
    """

    """
    def __init__(self):
        self._last_response = None
        self._last_query = None
        
        index_ref = pt.IndexRef.of('../wtr/index/data.properties')
        self._index =  pt.IndexFactory.of(index_ref)
        
        conn_string = 'postgresql://user:pass@localhost:5432/' + "webtables"
        engine = create_engine(conn_string)
        Session = sessionmaker(bind=engine)
        self._session = Session()
    
    def issue_query(self, query, num_results=100):
        """
        Allows one to issue a query to the underlying search engine. 
        """

        bm25 = pt.BatchRetrieve(self._index , wmodel='BM25', num_results=num_results)
        results = bm25.search(query.terms.decode('UTF-8'))
 
        response = Response(query_terms=query.terms.decode('UTF-8'), query=query)
        
        for result in results.iterrows():
            
            _docno = result[1].docno
            record = self._session.query(Table).filter_by(docno=_docno).first()

            if record:
                response.add_result(title=' '.join([record.pageTitle,record.title]),
                                    url=record.url,
                                    summary=' '.join([record.textBefore,record.textAfter]),
                                    docid=_docno,
                                    rank=result[1]['rank'] + 1,
                                    score=result[1].score,
                                    content=record.table_content,
                                    whooshid=_docno)
            
        response.result_total = len(results)
        
        self._last_query = query
        self._last_response = response
        
        return response
    
    def get_document(self, document_id):
        """
        Retrieves a Document object for the given document specified by parameter document_id.
        """
        
        record = self._session.query(Table).filter_by(docno=document_id.decode('utf-8')).first()
        title = ' '.join([record.pageTitle, record.title])
        content = record.table_content
        document = Document(id=document_id, title=title, content=content, doc_id=document_id)
        
        return document
