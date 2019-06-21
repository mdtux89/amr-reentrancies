import pickle
import re
import random
import argparse

def main(prefix, verbose):
    alldependencies = pickle.load(open(prefix + ".dependencies.p", "rb"))
    allalignments = pickle.load(open(prefix + ".alignments.p", "rb"))
    allrelations = pickle.load(open(prefix + ".relations.p", "rb"))
    allcorefs = pickle.load(open(prefix + ".corefs.p", "rb"))
    alltokens = pickle.load(open(prefix + ".tokens.p", "rb"))
    allgraphs = open(prefix + ".graphs").read().split('\n\n')
    controlverbs = open('controlverbs.txt').read().splitlines()
    verbalized = open('verbalized.txt').read().splitlines()

    total = 0
    coreference = 0
    control = 0
    coordination = 0
    verbalization = 0
    rest = []

    for dependencies, alignments, relations, corefs, tokens, graphs in \
            zip(alldependencies, allalignments, allrelations, \
                allcorefs, alltokens, allgraphs):
        mentions = {}
        reent_nodes = []
        for r in relations:
            if not r[2].isConst:
                if r[2].var in mentions:
                    mentions[r[2].var] += 1
                    reent_nodes.append(r[2].var)
                    total += 1
                else:
                    mentions[r[2].var] = 1

        for c in corefs:
            variables = []
            for i in range(corefs[c][0][0], corefs[c][0][1]):
                for x in alignments[i]:
                    if x.var is not None:
                        variables.append(x.var)
            for v in variables:
                for i in range(len(corefs[c])):
                    if v in reent_nodes:
                        coreference += 1
                        reent_nodes.remove(v)
                        corefs[c].pop(0)


        for d in dependencies:       
            if d[1] in ['xcomp', 'ccomp', 'advcl']:
                if len(alignments[d[0]]) != 0 and len(alignments[d[2]]) != 0:
                    l1 = [x[2].var for x in relations \
                          if x[0] == alignments[d[0]][0]]
                    l2 = [x[2].var for x in relations \
                          if x[0] == alignments[d[2]][0]]
                    for x in l1:
                        if x in l2 and x in reent_nodes:
                            control += 1
                            reent_nodes.remove(x)    

        seen = []
        for r in relations:
            if r[0].concept in ['and', 'contrast-01', 'for', 'nor', \
                        'or', 'so', 'yet'] and r[0] not in seen:
                seen.append(r[0])
                nodes = []
                for r2 in relations:
                    if r2[0] == r[0]:
                            nodes.append(r2[2])
                children = []
                for n in nodes:
                    children.append([r2[2] for r2 in relations if r2[0] == n])
                if len(children) == 1:
                    continue
                overlap = list(reduce(
                        lambda i, j: i & j, (set(x) for x in children)
                ))
                overlap = [o for o in overlap if o.isConst == False]
                for n in overlap:
                    if n.var in reent_nodes:
                        coordination += 1
                        reent_nodes.remove(n.var)  

        for d in dependencies:
            if len(alignments[d[0]]) != 0 and len(alignments[d[2]]) != 0:
                concept = alignments[d[2]][0].concept
                reg = re.match(r'.*-[0-9][0-9]*$', concept)
                if not alignments[d[2]][0].token.pos.startswith('V') \
                        and reg is not None:
                    l1 = [x[2].var for x in relations \
                          if x[0] == alignments[d[0]][0]]
                    l2 = [x[2].var for x in relations \
                          if x[0] == alignments[d[2]][0]]
                    for x in l1:
                        if x in l2 and x in reent_nodes:
                            verbalization += 1
                            reent_nodes.remove(x)

        if reent_nodes != [] and verbose:
            rest.append((
                    reent_nodes, graphs, 
                    ' '.join([t.word for t in tokens]), 
                    dependencies, 
                    alignments, 
                    corefs
            ))

    if verbose:
        random.shuffle(rest)
        for example in rest:
            print 'Reentrancies:'
            print example[0]
            print 'AMR:'
            print example[1]
            print 'Sentence:'
            print example[2]
            print 'Dependencies:'
            print example[3]
            print 'Alignments:'
            print example[4]
            print 'Coreferences:'
            print example[5]
            print

    print 'Coreference', coreference / float(total) * 100
    print 'Control', control / float(total) * 100
    print 'Coordination', coordination / float(total) * 100
    print 'Verbalization', verbalization / float(total) * 100

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Arguments.')
    parser.add_argument('-verbose', action='store_true')    
    parser.add_argument('-prefix', type=str, nargs='?', required=True)
    args = parser.parse_args()
    main(args.prefix, args.verbose)