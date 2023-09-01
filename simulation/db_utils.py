from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Text, ARRAY, FLOAT

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

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
    
class WapoQueries(Base):
    __tablename__ = 'wapo_doc2queries'
    docno = Column(String, primary_key=True)
    querygen = Column(ARRAY(Text))

    def __repr__(self):
        repr_str = f"docno={self.docno}, query={self.querygen}"
        return repr_str
    
class WapoDocEmbeddings(Base):
    __tablename__ = 'wapo_docembeddings'
    docno = Column(String, primary_key=True)
    embedding = Column(ARRAY(FLOAT))

    def __repr__(self):
        repr_str = f"docno={self.docno}, embedding={self.embedding}"
        return repr_str

def parse_wapo_entry(entry):
    doc_id = entry.doc_id
    url = entry.url
    title = entry.title
    author = entry.author
    kicker = entry.kicker
    body = entry.body

    return {"doc_id" : doc_id, "url" : url, "title" : title, "author" : author, "kicker" : kicker, "body" : body}

def gen_session(server_address = 'postgresql://root@postgres:5432/', db_name="wapo"):
    conn_string = server_address + db_name
    engine = create_engine(conn_string)

    Session = sessionmaker(bind=engine)
    return Session()

def get_wapo_entry(session, doc_id):
    return session.get(WapoEntry, doc_id)

def get_wapo_doc2query(session, doc_id):
    return session.get(WapoQueries, doc_id)

def get_wapo_emb(session, docno):
    return session.get(WapoDocEmbeddings, docno)

def refresh_db(server_address = 'postgresql://root@postgres:5432/', db_name="wapo"):
    engine = create_engine(server_address + db_name)
    Base.metadata.create_all(engine)