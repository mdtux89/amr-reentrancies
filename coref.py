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
    for i, tok in enumerate(doc):
        mentions = []
        try:
            #print(dir(tok._))
            #input()
            for c in tok._.coref_clusters:
                #print(dir(c))
                #input()
                mentions.append(c.main)
        except:
            pass
        for x in mentions:
            if tok not in x:
                if str(x) not in corefs:
                    corefs[str(x)] = []
                corefs[str(x)].append((x.start, x.end))
    allcorefs.append(corefs)

pickle.dump(allcorefs, open(prefix + ".corefs.p", "wb"), protocol=2)
