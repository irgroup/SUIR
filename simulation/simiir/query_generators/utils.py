import pyterrier as pt
import re

class IdfProvider():
    
    def __init__(self, index_path, stopwords):
        index_ref = pt.IndexRef.of(index_path)
        self._index =  pt.IndexFactory.of(index_ref)
        self._lex = self._index.getLexicon()
        self._stemmer = pt.TerrierStemmer.porter
        self._stopwords=stopwords

    def get_idf(self, term):
        if term in self._stopwords:
            return 2
        stemmed_term = self._stemmer.stem(term)
        df_term = self._lex[stemmed_term].getDocumentFrequency() if stemmed_term in self._lex else 0.5
        return 1/df_term
    
def token_2_term(token):
    return str.lower(re.sub("[\?\,\')]", "", token))

def get_stopwords(path="/workspace/data/stopword-list.txt"):
    stopwords = set()
    with open(path, "r") as f:
        for line in f.readlines():
            stopwords.add(line.strip())
    return stopwords

def filter_keywords(idf_provider : IdfProvider, keywords):
    keyword_set = []
    for keyword in keywords:
        keyword = token_2_term(keyword)
        if idf_provider.get_idf(keyword) < 0.5:
            keyword_set.append(keyword)
    
    return keyword_set