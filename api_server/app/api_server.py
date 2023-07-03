from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, String, Text, ARRAY
from sqlalchemy.ext.declarative import declarative_base
import os
import pyterrier as pt
import pandas as pd
import gc
import glob

app = Flask(__name__)
Base = declarative_base() 
session = None
bm25_models = {}
indices = {}
last_query = None

class TableQuery(Base):
    __tablename__ = 'tablequery'
    docno = Column(String, primary_key=True)
    querygen = Column(Text)
    
    def __repr__(self):
        repr_str = f"docno={self.docno}, query={self.querygen}"
        return repr_str

class TableQueries(Base):
    __tablename__ = 'doc2queries'
    docno = Column(String, primary_key=True)
    querygen = Column(ARRAY(Text))

    def __repr__(self):
        repr_str = f"docno={self.docno}, query={self.querygen}"
        return repr_str

def get_index_paths():
    indices_paths = [path for path in glob.glob("/app/indices/*") if "readme" not in path]
    index_path_dic = {}
    for path in indices_paths:
        index_path_dic[path.split('/')[-1]] = f"{path}/data.properties"

    return index_path_dic

def init():   
    if not pt.started():
        pt.init(boot_packages=["com.github.terrierteam:terrier-prf:-SNAPSHOT"])

    global bm25_models
    global session
    global indices

    index_path_dic = get_index_paths()
    for key, val in index_path_dic.items():
        index_ref = pt.IndexRef.of(val)
        indices[key] = pt.IndexFactory.of(index_ref)
        bm25_models[key] = pt.BatchRetrieve(indices[key] , wmodel='BM25', num_results=100)
        print(f"laoded {key} index")

    #engine = create_engine("postgresql://root@postgres:5432/webtables_db")
    #Session = sessionmaker(bind=engine)
    #session = Session()

@app.route("/doc2query/<docno_request>", methods=['GET'])
def response_d2q(docno_request: str):
    if docno_request:
        docno_request = docno_request.replace("$", "/")
        result = session.get(TableQueries, docno_request)
        if result:
            result = result.querygen
        else:
            return "docno not found"
    else:
        return "no argument given"

    return jsonify(
        response_d2q=result
    )

@app.route("/results_wapo/<query>", methods=['GET'])
def response_query(query: str):
    #Sgc.collect()
    results = bm25_models['wapo_v2'].search(query)
    global last_query

    last_query = query
    return jsonify(
        response_query=results.to_dict()
    )

@app.route("/results_rm3/<rel_docs>", methods=['GET'])
def response_query_rm3(rel_docs: str):
    
    global last_query

    if rel_docs == "no_rels":
        rel_docs = []
    else:
        rel_docs = set([rel_doc.replace("$", "/") for rel_doc in rel_docs.split(',')])

    # push rel docs to the top

    rel_pusher = pt.apply.doc_score(lambda row: 9000 if row['docno'] in rel_docs else row['score'])
    

    '''
    test_p = bm25 >> rel_pusher
    with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
        print(test_p.search(last_query))
    '''
    print(last_query)

    rm3_pipe = bm25 >> rel_pusher >> pt.rewrite.RM3(index) >> bm25
    results = rm3_pipe.search(last_query)

    last_query = results['query'][0]

    return jsonify(
        response_query=results.to_dict()
    )

if __name__ == '__main__':

    init()
    app.run(host='0.0.0.0', port=5000)

