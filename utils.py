import re
import copy
from collections import defaultdict
import smatch.amr as amr
from graph import Graph

def reentrancies(triples, v2c_dict):
    lst = []
    vrs = []
    for n in v2c_dict.keys():
        parents = [(l,v1,v2) for (l,v1,v2) in triples if v2 == n and l != "instance"]
        if len(parents) > 1:
            #extract triples involving this (multi-parent) node
            for t in parents:
                lst.append(t)
                vrs.extend([t[1],t[2]])
    #collect var/concept pairs for all extracted nodes
    dict1 = {}
    for i in v2c_dict:
         if i in vrs:
            dict1[i] = v2c_dict[i]
    return (lst, dict1)

def var2concept(amr):
    v2c = {}
    for n, v in zip(amr.nodes, amr.node_values):
        v2c[n] = v
    return v2c

def read_annotations(filename):
    annotations = []
    for annot in open(filename).read().strip().split('\n\n'):
        if len(annot.split('\n')) < 2:
            continue
        for line in annot.split('\n'):
            if line.startswith('# ::tok') or line.startswith('# ::snt'):
                sentence = line[8:]
        amr = ''.join([x for x in annot.split('\n') if not x.startswith('#')])
        annotations.append((sentence, amr))
    return annotations

def from_annot(line):
    try:
        amr_pred = amr.AMR.parse_AMR_line(line)
        amr_pred.rename_node('b')
        dict_pred = var2concept(amr_pred)
        triples_pred = [t for t in amr_pred.get_triples()[1] if t[0] != 'TOP']
        triples_pred.extend([t for t in amr_pred.get_triples()[2] if t[0] != 'TOP'])
        return triples_pred, dict_pred
    except:
        return None

def get_raw_data(gold_file, prediction_file, alignment_file):
    reg = re.compile(r'(\w+)\(.+\)-(\w+)\(.+\)')
    gold = read_annotations(gold_file)
    pred = read_annotations(prediction_file)
    data = []
    for annot_gold, annot_pred, alignment in zip(gold, pred, open(alignment_file)):
        sentence, amr_pred = annot_pred
        amr_pred = amr.AMR.parse_AMR_line(amr_pred)
        amr_pred.rename_node('b')
        dict_pred = var2concept(amr_pred)
        triples_pred = [t for t in amr_pred.get_triples()[1] if t[0] != 'TOP']
        triples_pred.extend([t for t in amr_pred.get_triples()[2] if t[0] != 'TOP'])
        
        _, amr_gold = annot_gold
        amr_gold = amr.AMR.parse_AMR_line(amr_gold)
        amr_gold.rename_node('a')
        dict_gold = var2concept(amr_gold)
        triples_gold = [t for t in amr_gold.get_triples()[1] if t[0] != 'TOP']
        triples_gold.extend([t for t in amr_gold.get_triples()[2] if t[0] != 'TOP'])
        
        alignment_lst = []
        for pair in alignment.split():
            if 'Null' not in pair:
                vs = reg.findall(pair)
                alignment_lst.append(vs[0][0] + '-' + vs[0][1])
        
        src = Graph(triples_pred, dict_pred, annot_pred[1])
        tgt = Graph(triples_gold, dict_gold, annot_gold[1])
        data.append((src, tgt, sentence, alignment_lst))
    return data

def oracle(src, tgt, align_map, var_permutations, action_type):
    actions = defaultdict(list)
    src_children = []
    mentions = defaultdict(int)
    coord_nodes = [x for x in src.nodes if src.nodes[x] in 
                   ['and', 'contrast-01', 'for', 'nor', 'or', 'so', 'yet']
                  ]
    
    for x in src.edges:
        mentions[x] += 1
        for item in src.edges[x]:
            mentions[item[0]] += 1
            src_children.append((x, item[0]))

    tgt_children = []
    for x in tgt.edges:
        for item in tgt.edges[x]:
            tgt_children.append((x, item[0]))
    
    for s_a, s_b, s_c in var_permutations:
        t_a = align_map[s_a]
        t_b = align_map[s_b]
        t_c = align_map[s_c]
        
        # merge two concepts
        if action_type == 'merge' or action_type == 'merge_coord':
            for s_d in src.nodes:
                if s_d not in [s_a, s_b, s_c] and s_d in align_map:
                    t_d = align_map[s_d]
                    if((s_a, s_b) in src_children and \
                            (s_c, s_d) in src_children and \
                            (s_c, s_b) not in src_children and \
                            (t_a, t_b) in tgt_children and \
                            (t_c, t_b) in tgt_children and \
                            (t_c, t_d) not in tgt_children):                
                        if mentions[s_d] > 1 and mentions[s_c] > 1:
                            lab = [x[1] for x in src.edges[s_c] if x[0] == s_d][0]
                            e1 = (s_c, s_d, src.nodes[s_c], src.nodes[s_d], lab)
                            mentions[s_d] -= 1
                            mentions[s_c] -= 1                        
                            lab = [x[1] for x in tgt.edges[t_c] if x[0] == t_b][0]
                            e2 = (s_c, s_b, tgt.nodes[t_c], tgt.nodes[t_b], lab)    
                            
                            if action_type == 'merge_coord':
                                for s_i in coord_nodes:
                                    if (s_a, s_i) in src_children and \
                                            (s_c, s_i) in src_children:
                                        if (e1, e2) not in actions['merge_coord']:
                                            actions['merge_coord'].append((e1, e2)) 
                                            break
                            elif action_type == 'merge':
                                if (e1, e2) not in actions['merge']:
                                    actions['merge'].append((e1, e2)) 
                            
        if action_type == 'merge_rmnode' or action_type == 'merge_coord_rmnode':
            for s_d in src.nodes:
                if s_d not in [s_a, s_b, s_c] and s_d not in align_map:
                    if (s_a, s_b) in src_children and \
                            (s_c, s_d) in src_children and \
                            (s_c, s_b) not in src_children and \
                            (t_a, t_b) in tgt_children and \
                            (t_c, t_b) in tgt_children:
                        if mentions[s_d] == 1 and s_d.startswith('b'):
                            # second check is because otherwise could erronously remove a 
                            # new node that was introduced by one of the other actions..                            
                            lab = [x[1] for x in src.edges[s_c] if x[0] == s_d][0]
                            e1 = (s_c, s_d, src.nodes[s_c], src.nodes[s_d], lab)
                            mentions[s_d] -= 1
                            mentions[s_c] -= 1                        
                            lab = [x[1] for x in tgt.edges[t_c] if x[0] == t_b][0]
                            e2 = (s_c, s_b, tgt.nodes[t_c], tgt.nodes[t_b], lab)    
                            
                            if action_type == 'merge_coord_rmnode':
                                for s_i in coord_nodes:
                                    if (s_a, s_i) in src_children and \
                                            (s_c, s_i) in src_children:
                                        if (e1, e2) not in actions['merge_coord_rmnode']:
                                            actions['merge_coord_rmnode'].append((e1, e2)) 
                                            break
                            elif action_type == 'merge_rmnode':
                                if (e1, e2) not in actions['merge_rmnode']:
                                    actions['merge_rmnode'].append((e1, e2))                  

        #split two concepts with a new node
        if action_type == 'split' or action_type == 'split_coord':        
            for s_d in src.nodes:
                if s_d not in [s_a, s_b, s_c] and s_d in align_map:
                    t_d = align_map[s_d]
                    if (s_a, s_b) in src_children and \
                            (s_c, s_b) in src_children and \
                            (s_c, s_d) not in src_children and \
                            (t_a, t_b) in tgt_children and \
                            (t_c, t_b) not in tgt_children and \
                            (t_c, t_d) in tgt_children:
                        lab = [x[1] for x in src.edges[s_c] if x[0] == s_b][0]
                        e1 = (s_c, s_b, src.nodes[s_c], src.nodes[s_b], lab)
                        lab = [x[1] for x in tgt.edges[t_c] if x[0] == t_d][0]
                        e2 = (s_c, s_d, tgt.nodes[t_c], tgt.nodes[t_d], lab)
                        
                        if action_type == 'split_coord':
                            for s_i in coord_nodes:
                                if (s_a, s_i) in src_children and \
                                        (s_c, s_i) in src_children:
                                    if (e1, e2) not in actions['split_coord']:
                                        actions['split_coord'].append((e1, e2)) 
                                        break
                        elif action_type == 'split':
                            if (e1, e2) not in actions['split']:
                                actions['split'].append((e1, e2))                        
                
        #split two concepts with an old node
        if action_type == 'split_addnode' or action_type == 'split_coord_addnode':
            for t_d in tgt.nodes:
                if t_d not in [t_a, t_b, t_c]:
                    if t_d not in align_map.values() and \
                            (s_a, s_b) in src_children and \
                            (s_c, s_b) in src_children and \
                            (t_a, t_b) in tgt_children and \
                            (t_c, t_b) not in tgt_children and \
                            (t_c, t_d) in tgt_children:
                        lab = [x[1] for x in src.edges[s_c] if x[0] == s_b][0]
                        e1 = (s_c, s_b, src.nodes[s_c], src.nodes[s_b], lab)                      
                        lab = [x[1] for x in tgt.edges[t_c] if x[0] == t_d][0]
                        e2 = (s_c, t_d, tgt.nodes[t_c], tgt.nodes[t_d], lab)

                        if action_type == 'split_coord_addnode':
                            for s_i in coord_nodes:
                                if (s_a, s_i) in src_children and \
                                        (s_c, s_i) in src_children:
                                    if (e1, e2) not in actions['split_coord_addnode']:
                                        actions['split_coord_addnode'].append((e1, e2)) 
                                        break
                        elif action_type == 'split_addnode':
                            if (e1, e2) not in actions['split_addnode']:
                                actions['split_addnode'].append((e1, e2))               
        
        # add a sibling edge
        if action_type == 'add_sibling':
            if (s_a, s_b) in src_children and \
                    (s_a, s_c) in src_children and \
                    (s_b, s_c) not in src_children and \
                    (t_a, t_c) in tgt_children and \
                    (t_a, t_b) in tgt_children and \
                    (t_b, t_c) in tgt_children:
                lab = [x[1] for x in tgt.edges[t_b] if x[0] == t_c][0]
                e = (s_b, s_c, tgt.nodes[t_b], tgt.nodes[t_c], lab)
                if e not in actions['add_sibling']:
                    actions['add_sibling'].append(e)
                    
        if action_type == 'add_sibling_addnode':                    
            for t_d in tgt.nodes:
                if t_d not in [t_a, t_b, t_c]:
                    if t_d not in align_map.values() and \
                            (s_a, s_b) in src_children and \
                            (t_a, t_b) in tgt_children and \
                            (t_a, t_d) in tgt_children and \
                            (t_b, t_d) in tgt_children:
                        lab = [x[1] for x in tgt.edges[t_b] if x[0] == t_d][0]
                        e = (s_b, t_d, tgt.nodes[t_b], tgt.nodes[t_d], lab)
                        if e not in actions['add_sibling_addnode']:               
                            actions['add_sibling_addnode'].append(e)
                    
        # remove a sibling edge
        if action_type == 'remove_sibling':
            if (s_a, s_b) in src_children and \
                    (s_a, s_c) in src_children and \
                    (s_b, s_c) in src_children and \
                    (t_a, t_c) in tgt_children and \
                    (t_a, t_b) in tgt_children and \
                    (t_b, t_c) not in tgt_children:
                if mentions[s_b] > 1 and mentions[s_c] > 1:
                    lab = [x[1] for x in src.edges[s_b] if x[0] == s_c][0]
                    e = (s_b, s_c, src.nodes[s_b], src.nodes[s_c], lab)
                    mentions[s_c] -= 1
                    mentions[s_b] -= 1                    
                    if e not in actions['remove_sibling']:
                        actions['remove_sibling'].append(e)
                    
        if action_type == 'remove_sibling_rmnode':
            for s_d in tgt.nodes:
                if s_d not in [s_a, s_b, s_c] and s_d not in align_map:
                    if (s_a, s_b) in src_children and \
                            (s_a, s_d) in src_children and \
                            (s_b, s_d) in src_children and \
                            (t_a, t_b) in tgt_children:
                        if mentions[s_d] == 1 and s_d.startswith('b'):
                            lab = [x[1] for x in src.edges[s_b] if x[0] == s_d][0]
                            e = (s_b, s_d, src.nodes[s_b], src.nodes[s_d], lab)
                            mentions[s_d] -= 1
                            mentions[s_b] -= 1                              
                            if e not in actions['remove_sibling_rmnode']:
                                actions['remove_sibling_rmnode'].append(e)                    

        # additions between existing nodes
        if action_type == 'add':
            if (s_a, s_b) in src_children and \
                    (s_c, s_b) not in src_children and \
                    (t_a, t_b) in tgt_children and \
                    (t_c, t_b) in tgt_children:
                lab = [x[1] for x in tgt.edges[t_c] if x[0] == t_b][0]
                e = (s_c, s_b, tgt.nodes[t_c], tgt.nodes[t_b], lab)
                if e not in actions['add']:
                    actions['add'].append(e)
            
        # additions between existing node and a new node
        if action_type == 'add_addnode':
            for t_d in tgt.nodes:
                if t_d not in [t_a, t_b, t_c]:
                    if t_d not in align_map.values() and \
                            (s_a, s_b) in src_children and \
                            (t_a, t_b) in tgt_children and \
                            (t_d, t_b) in tgt_children:
                        lab = [x[1] for x in tgt.edges[t_d] if x[0] == t_b][0]
                        e = (t_d, s_b, tgt.nodes[t_d], tgt.nodes[t_b], lab)
                        # align_map[t_d] = t_d
                        if e not in actions['add_addnode']:
                            actions['add_addnode'].append(e)            
            
        # removals
        if action_type == 'remove':
            if (s_a, s_b) in src_children and \
                    (s_c, s_b) in src_children and \
                    (t_a, t_b) in tgt_children and \
                    (t_c, t_b) not in tgt_children:
                if mentions[s_c] > 1 and mentions[s_b] > 1:
                    lab = [x[1] for x in src.edges[s_c] if x[0] == s_b][0]
                    e = (s_c, s_b, src.nodes[s_c], src.nodes[s_b], lab)
                    mentions[s_c] -= 1
                    mentions[s_b] -= 1
                    if e not in actions['remove']:
                        actions['remove'].append(e)

        if action_type == 'remove_rmnode': 
            for s_d in src.nodes:
                if s_d not in [s_a, s_b, s_c] and s_d not in align_map:                   
                    if (s_a, s_b) in src_children and \
                            (s_d, s_b) in src_children:
                        if mentions[s_d] == 1 and s_d.startswith('b'):
                            # second check is because otherwise could erronously remove a 
                            # new node that was introduced by one of the other actions..
                            lab = [x[1] for x in src.edges[s_d] if x[0] == s_b][0]
                            e = (s_d, s_b, src.nodes[s_d], src.nodes[s_b], lab)
                            mentions[s_d] -= 1
                            mentions[s_b] -= 1
                            if e not in actions['remove_rmnode']:
                                actions['remove_rmnode'].append(e)                                
    return actions

def _to_string(triples, root, level, last_child, seen, prefix, indexes, nodes):
    if len(root.split("/")) == 2:
        conc = root.split("/")[1].strip()
    else:
        conc = root.split()[0]
    children = [t for t in triples if str(t[0]) == root.split()[0]]
    if root in seen:
        root = root.split()[0]
        children = []
    else:
        var = root
        if " / " in root:
            var = root.split()[0]
        nodes.append((var,conc))
        indexes[var].append(prefix)
    if " / " in root:
        seen.append(root)
        graph = "(" + root
        if len(children) > 0:
            graph += "\n"
        else:
            graph += ")"
    else:
        graph = root
    j = 0
    for k, t in enumerate(children):
        if str(t[0]) == root.split()[0]:
            next_r = t[3]
            if t[4] != "":
                next_r += " / " + t[4]
            for i in range(0, level):
                graph += "    "
            seen2 = copy.deepcopy(seen)
            to_str = _to_string(
                triples, next_r, level + 1, k == len(children) - 1, 
                seen, prefix + "." + str(j), indexes, nodes
            )
            graph += t[2] + " " + to_str[0]
            if next_r not in seen2 or " / " not in next_r:
                j += 1
    if len(children) > 0:
        graph += ")"
    if not last_child:
        graph += "\n"

    return graph, indexes, nodes

def to_string(triples, root):
    children = [t for t in triples if str(t[0]) == root]
    assert(len(children)==1)
    if children[0][4] == "":
        return "(e / emptygraph)", defaultdict(list), []
    return _to_string(
        triples, children[0][3] + " / " + children[0][4], 1, False, 
        [], "0", defaultdict(list), []
    )