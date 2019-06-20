from collections import defaultdict

class Graph:
    def __init__(self, tuples, dic, annot=''):
        self.annot = []
        for w in annot.split():
            if (w.startswith('"') and w.endswith('"')) or \
                    (w.startswith("'") and w.endswith("'")):
                self.annot.append(w)
            else:
                opens = [c for c in w if c == '(']
                closes = [c for c in w if c == ')']
                self.annot.extend(opens)
                self.annot.append(w[len(opens): len(w) - len(closes)])
                self.annot.extend(closes)
        self.nodes = defaultdict(str)
        self.edges = defaultdict(list)
        self.var_idx = 0
        for t in tuples:
            l = t[0]
            v1, c1 = t[1], t[1]
            v2, c2 = t[2], t[2]
            if t[1] in dic:
                c1 = dic[t[1]]
            if t[2] in dic:
                c2 = dic[t[2]]
            self.edges[v1].append((v2, l))
            self.nodes[v1] = c1
            self.nodes[v2] = c2
        self.smatch_relations = (tuples, dic)
