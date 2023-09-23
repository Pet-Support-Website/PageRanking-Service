from flask import Flask, request
from flask_cors import CORS
from PRxSolr import Indexer
import pandas as pd
import numpy as np
import time

app = Flask(__name__)
CORS(app, resources={r"/search_solr": {"origins": "*"}})
appsolr = Indexer()
appsolr.run_indexer()
# tags = ["dog","headline","nutrient","general","health","exercise","training","grooming","handling","shelter","vaccination","littering","supply","aggression","behavior issues","barking","destructive","food guarding","howling","mounting","anxiety","whining","diseases","cat","meowing","older","urine marking","bird","reptile","chameleon","snake","tortoise","fish","danio","goldfish","koi","rabbit","rodents"]


@app.route('/search_solr', methods=['GET'])
def search_solr():
    start = time.time()
    response_object = {'status': 'success'}
    argList = request.args.to_dict(flat=False)
    query_term=argList['query'][0].replace("202","+")
    print(query_term)
    results = appsolr.solr.search('text:'+query_term, **{'defType': 'edismax', 'boost': 'mul(query($q),field(pagerank,min))'})
    end = time.time()
    filtered_results = []
    index = 0;
    for result in results:
        if "article" in result['url'][0]:
            filtered_results.insert(index, result)
            index+=1

    for result in filtered_results:
        print(result)

    results_df = pd.DataFrame(np.hstack([[result['title'] for result in filtered_results], [result['url'] for result in filtered_results],
                                        [result['pagerank'] for result in filtered_results]]),
                              columns=['title', 'url', 'score'])

    response_object['total_hit'] = results.hits
    response_object['results'] = results_df.to_dict('records')
    response_object['elapse'] = end - start

    return response_object
if __name__ == '__main__':
    app.run(debug=True)
