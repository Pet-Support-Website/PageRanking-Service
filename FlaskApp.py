from flask import Flask, request
from PRxSolr import Indexer
import pandas as pd
import numpy as np
import time

app = Flask(__name__)
appsolr = Indexer()
appsolr.run_indexer()

@app.route('/search_solr', methods=['GET'])
def search_solr():
    start = time.time()
    response_object = {'status': 'success'}
    argList = request.args.to_dict(flat=False)
    query_term=argList['query'][0]
    results = appsolr.solr.search('text:'+query_term, **{'defType': 'edismax', 'boost': 'mul(query($q),field(pagerank,min))'})
    for result in results:
         print(result)
    end = time.time()
    results_df = pd.DataFrame(np.hstack([[result['title'] for result in results], [result['url'] for result in results],
                                        [result['pagerank'] for result in results]]),
                              columns=['title', 'url', 'score'])

    response_object['total_hit'] = results.hits
    response_object['results'] = results_df.to_dict('records')
    response_object['elapse'] = end - start

    return response_object
if __name__ == '__main__':
    app.run(debug=True)
