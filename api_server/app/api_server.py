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
session_ds = None
session_d2q = None
bm25_models = {}
indices = {}
last_query = None
    
class WapoEntry(Base):
    __tablename__ = 'wapo'
    doc_id = Column(String, primary_key=True)
    url = Column(String)
    title = Column(String)
    author = Column(String)
    kicker = Column(Text)
    body = Column(Text)
    
    def __repr__(self):
        repr_str = f"doc_id={self.doc_id}, url={self.url}, title={self.title}, author={self.author},"\
        f"kicker={self.kicker}, body={self.body}"
        
        return repr_str
    
class NytEntry(Base):
    __tablename__ = 'nyt'
    doc_id = Column(String, primary_key=True)
    headline = Column(String)
    body = Column(String)
    
    def __repr__(self):
        repr_str = f"doc_id={self.doc_id}, headline={self.headline}, body={self.body}"

        return repr_str

class WapoDoc2Qeury(Base):
    __tablename__ = 'wapo_doc2queries'
    docno = Column(String, primary_key=True)
    querygen = Column(ARRAY(Text))

    def __repr__(self):
        repr_str = f"docno={self.docno}, query={self.querygen}"
        return repr_str

class NytDoc2Qeury(Base):
    __tablename__ = 'nyt_doc2queries'
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
    global session_ds
    global session_d2q
    global indices

    index_path_dic = get_index_paths()
    for key, val in index_path_dic.items():
        index_ref = pt.IndexRef.of(val)
        indices[key] = pt.IndexFactory.of(index_ref)
        bm25_models[key] = pt.BatchRetrieve(indices[key] , wmodel='BM25', num_results=100)
        print(f"laoded {key} index")

    engine_ds = create_engine("postgresql://root@postgres:5432/datasets")
    Session_ds = sessionmaker(bind=engine_ds)
    session_ds = Session_ds()

    engine_d2q = create_engine("postgresql://root@postgres:5432/doc2queries")
    Session_d2q = sessionmaker(bind=engine_d2q)
    session_d2q = Session_d2q()

@app.route("/results_wapo/<query>", methods=['GET'])
def response_query_wapo(query: str):
    #Sgc.collect()
    results = bm25_models['wapo_v2'].search(query)
    global last_query

    last_query = query
    return jsonify(
        response_query_wapo=results.to_dict()
    )

#TODO implement nyt index
@app.route("/results_nyt/<query>", methods=['GET'])
def response_query_nyt(query: str):
    #Sgc.collect()
    results = bm25_models['nyt'].search(query)
    global last_query

    last_query = query
    return jsonify(
        response_query_nyt=results.to_dict()
    )

@app.route("/doc2query_wapo/<docno_request>", methods=['GET'])
def response_d2q_wapo(docno_request: str):
    if docno_request:
        docno_request = docno_request.replace("$", "/")
        result = session_d2q.get(WapoDoc2Qeury, docno_request)
        if result:
            result = result.querygen
        else:
            return "docno not found"
    else:
        return "no argument given"

    return jsonify(
        response_d2q_wapo=result
    )

@app.route("/doc2query_nyt/<docno_request>", methods=['GET'])
def response_d2q_nyt(docno_request: str):
    if docno_request:
        docno_request = docno_request.replace("$", "/")
        result = session_d2q.get(NytDoc2Qeury, docno_request)
        if result:
            result = result.querygen
        else:
            return "docno not found"
    else:
        return "no argument given"

    return jsonify(
        response_d2q_nyt=result
    )


if __name__ == '__main__':

    init()
    app.run(host='0.0.0.0', port=5001)

