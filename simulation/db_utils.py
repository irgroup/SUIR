from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Text, ARRAY

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
    

def parse_wapo_entry(entry):
    doc_id = entry.doc_id
    url = entry.url
    title = entry.title
    author = entry.author
    kicker = entry.kicker
    body = entry.body

    return {"doc_id" : doc_id, "url" : url, "title" : title, "author" : author, "kicker" : kicker, "body" : body}

def get_wapo_entry(session, doc_id):
    return session.get(WapoEntry, doc_id)