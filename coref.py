import spacy
import sys
import pickle

nlp = spacy.load('en')

import neuralcoref

neuralcoref.add_to_pipe(nlp)

prefix = sys.argv[1]
alltokens = pickle.load(open(prefix + ".tokens.p", "rb"), encoding="latin1")

allcorefs = []
for i, tokens in enumerate(alltokens):
    print(i)
    sentence = ' '.join([w.word for w in tokens])
    doc = nlp(sentence.strip())
    corefs = {}
    for cluster in doc._.coref_clusters:
        corefs[str(cluster.main)] = (
            len([str(x) for x in cluster if x != cluster.main]),
            cluster.main.start,
            cluster.main.end
        )
    allcorefs.append(corefs)

pickle.dump(allcorefs, open(prefix + ".corefs.p", "wb"), protocol=2)
