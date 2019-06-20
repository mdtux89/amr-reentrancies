import pickle
import copy
import argparse
import random
from collections import defaultdict
from utils import to_string, _to_string, reentrancies, from_annot
import smatch.smatch_fromlists as smatch
random.seed(123)

def apply_action_pattern(old_graphs, gold_graphs, all_actions, action_type):
    new_graphs, new_graphs_reentrancies = [], []
    for src, gold in zip(old_graphs, gold_graphs):
        new_lst, new_dic = copy.deepcopy(src)           
        src_children = []
        for x in new_lst:       
            src_children.append((x[1], x[2]))        
        if action_type == 'add':            
            cur_vars = list(new_dic.keys())
            for action in all_actions:
                _, a, b, c, _, _, _, lab = action.split()
                dic_inv = defaultdict(list)
                for k in new_dic:
                    dic_inv[new_dic[k]].append(k)
                s_a, s_b, s_c = None, None, None
                if a in dic_inv and len(dic_inv[a]) > 0:
                    s_a = dic_inv[a][0]
                    dic_inv[a].pop(0)
                if b in dic_inv and len(dic_inv[b]) > 0:
                    s_b = dic_inv[b][0]
                    dic_inv[b].pop(0)                    
                if c in dic_inv and len(dic_inv[c]) > 0:
                    s_c = dic_inv[c][0]
                    dic_inv[c].pop(0)
                if s_a is not None and s_b is not None and s_c is not None:
                    if (s_a, s_b) in src_children: 
                        if (s_c, s_b) not in src_children:
                            new_lst.append((lab, s_c, s_b))
        new_graphs.append((new_lst, new_dic))
        new_graphs_reentrancies.append(reentrancies(new_lst, new_dic))

    return new_graphs, new_graphs_reentrancies

def apply_action_random(old_graphs, gold_graphs, all_actions, action_type):
    new_graphs, new_graphs_reentrancies = [], []
    for src, gold in zip(old_graphs, gold_graphs):
        new_lst, new_dic = copy.deepcopy(src)           
        if action_type == 'add':
            for i in range(1):
                v1 = random.choice(list(new_dic.keys()))
                v2 = random.choice(list(new_dic.keys()))
                l = random.choice(['ARG0'])
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))
        new_graphs.append((new_lst, new_dic))
        new_graphs_reentrancies.append(reentrancies(new_lst, new_dic))
    return new_graphs, new_graphs_reentrancies

def apply_action_s2s(old_graphs, gold_graphs, all_actions, action_type):
    new_graphs, new_graphs_reentrancies = [], []
    for src, gold, actions in zip(old_graphs, gold_graphs, all_actions):
        new_lst, new_dic = copy.deepcopy(src)          
        if action_type == 'add':
            for e in actions['add']:
                c1, c2, l = e
                v1, v2 = None, None
                for k in new_dic:
                    if new_dic[k] == c1:
                        v1 = k
                    if new_dic[k] == c2:
                        v2 = k
                if v1 is not None and v2 is not None:
                    if (l, v1, v2) not in new_lst:
                        new_lst.append((l, v1, v2))              
        new_graphs.append((new_lst, new_dic))
        new_graphs_reentrancies.append(reentrancies(new_lst, new_dic))
    return new_graphs, new_graphs_reentrancies


def apply_action_oracle(old_graphs, gold_graphs, all_actions, action_type):
    new_graphs, new_graphs_reentrancies = [], []
    counts = 0
    for src, gold, actions in zip(old_graphs, gold_graphs, all_actions):
        new_lst, new_dic = copy.deepcopy(src)
        if action_type == 'split':
            for rem, add in actions['split']:
                v1, v2, _, _, l = rem
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1
                v1, v2, _, _, l = add
                if (l, v1, v2) not in new_lst:                
                    new_lst.append((l, v1, v2))                    
                    counts += 1                    
        elif action_type == 'split_addnode':
            for rem, add in actions['split_addnode']:
                v1, v2, _, _, l = rem
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1                    
                v1, v2, _, c2, l = add
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))
                    new_dic[v2] = c2             
                    counts += 1                    
        if action_type == 'split_coord':
            for rem, add in actions['split_coord']:
                v1, v2, _, _, l = rem
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1           
                v1, v2, _, _, l = add
                if (l, v1, v2) not in new_lst:                
                    new_lst.append((l, v1, v2))
                    counts += 1                    
        if action_type == 'split_coord_rmnode':
            for rem, add in actions['split_coord_rmnode']:
                v1, v2, _, _, l = rem
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1                    
                v1, v2, _, c2, l = add
                if (l, v1, v2) not in new_lst:                
                    new_lst.append((l, v1, v2))   
                    new_dic[v2] = c2   
                    counts += 1                    
        elif action_type == 'add':
            for e in actions['add']:
                v1, v2, _, _, l = e
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))
                    counts += 1                    
        elif action_type == 'add_sibling':
            for e in actions['add_sibling']:
                v1, v2, _, _, l = e
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))   
                    counts += 1                    
        elif action_type == 'add_sibling_addnode':
            for e in actions['add_sibling_addnode']:
                v1, v2, c1, _, l = e
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))
                    new_dic[v1] = c1
                    counts += 1                    
        elif action_type == 'add_addnode':
            for e in actions['add_addnode']:
                v1, v2, c1, _, l = e
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))
                    new_dic[v1] = c1            
                    counts += 1                    
        elif action_type == 'merge':
            for rem, add in actions['merge']:
                v1, v2, _, _, l = rem
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1                    
                v1, v2, _, _, l = add
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))
                    counts += 1                    
        elif action_type == 'merge_rmnode':
            for rem, add in actions['merge_rmnode']:
                v1, v2, _, _, l = rem
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1                    
                v1, v2, _, _, l = add
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))
                    counts += 1                    
        elif action_type == 'merge_coord':
            for rem, add in actions['merge_coord']:
                v1, v2, _, _, l = rem
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1                    
                v1, v2, _, _, l = add
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))                    
                    counts += 1                    
        elif action_type == 'merge_coord_rmnode':
            for rem, add in actions['merge_coord_rmnode']:
                v1, v2, _, _, l = rem
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1                    
                v1, v2, _, _, l = add
                if (l, v1, v2) not in new_lst:
                    new_lst.append((l, v1, v2))                       
                    counts += 1                    
        elif action_type == 'remove':
            for e in actions['remove']:
                v1, v2, _, _, l = e
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1                    
        elif action_type == 'remove_sibling':
            for e in actions['remove_sibling']:
                v1, v2, _, _, l = e
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))
                    counts += 1                    
        elif action_type == 'remove_sibling_rmnode':
            for e in actions['remove_sibling_rmnode']:
                v1, v2, _, _, l = e
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))                    
                    counts += 1                    
        elif action_type == 'remove_rmnode':
            for e in actions['remove_rmnode']:
                v1, v2, _, _, l = e
                if (l, v1, v2) in new_lst:
                    new_lst.remove((l, v1, v2))                
                    counts += 1                    
        new_graphs.append((new_lst, new_dic))
        new_graphs_reentrancies.append(reentrancies(new_lst, new_dic))
    if action_type.startswith('merge') or action_type.startswith('split'):
        counts = counts / 2
    return new_graphs, new_graphs_reentrancies, counts

def main(args):
    data = pickle.load(open(args.data, "rb"))
    gold_graphs, old_graphs, new_graphs = [], [], []
    gold_graphs_reentrancies = []
    old_graphs_reentrancies = []
    new_graphs_reentrancies = []
    if args.method == 'ORACLE':
        actions = [x[2] for x in data]
    elif args.method == 'RANDOM':
        actions = None
    elif args.method == 'PATTERN':
        actions = open('patterns_train17_thresh.txt').read().splitlines()
    # else: # S2S
    #     actions = []
    #     for line in open(args.method):
    #         # actions.append(from_annot(line))
    #         if line.strip() == 'EMPTY':
    #             actions.append({args.action_type: []})
    #             continue
    #         else:
    #             words = line.strip().split()
    #             i = 0
    #             actions_line = []
    #             while i < len(words):
    #                 if i + 2 >= len(words) or \
    #                         'EMPTY' == words[i] or \
    #                         'EMPTY' == words[i + 1] or \
    #                         'EMPTY' == words[i + 2]:
    #                     i += 3
    #                     continue
    #                 actions_line.append(
    #                     (words[i], words[i + 1], words[i + 2])
    #                 )
    #                 i += 3
    #             actions.append({args.action_type: actions_line})
    counts = None
    for example in data:
        _, src, _, gold = example
        gold_graphs.append(gold)
        gold_graphs_reentrancies.append(reentrancies(gold[0], gold[1]))
        old_graphs.append(src)
        old_graphs_reentrancies.append(reentrancies(src[0], src[1]))
    
    if args.method == 'ORACLE':
        new_graphs, new_graphs_reentrancies, counts = apply_action_oracle(
            old_graphs, gold_graphs, actions, args.action_type
        )
    elif args.method == 'RANDOM':
        new_graphs, new_graphs_reentrancies = apply_action_random(
            old_graphs, gold_graphs, actions, args.action_type
        )
    elif args.method == 'PATTERN':
        new_graphs, new_graphs_reentrancies = apply_action_pattern(
            old_graphs, gold_graphs, actions, args.action_type
        )
    # else:  # S2S
    #     new_graphs, new_graphs_reentrancies_s2s = apply_action(
    #         old_graphs, gold_graphs, actions, args.action_type
    #     )
    if not args.silent:
        print 'Action type:', args.action_type
        if counts is not None:
            print 'Number of actions:', counts
        print 'Computing Smatch...'
        print 'Old Smatch score:', smatch.main(old_graphs, gold_graphs, True)[2]
        print 'Old Reentrancy score:', \
              smatch.main(old_graphs_reentrancies, gold_graphs_reentrancies, True)[2]
        print 'New Smatch score:', smatch.main(new_graphs, gold_graphs, True)[2]
        print 'New Reentrancy score:', \
              smatch.main(new_graphs_reentrancies, gold_graphs_reentrancies, True)[2]
    else:
        old_smatch_score = smatch.main(old_graphs, gold_graphs, True)[2]
        old_reentr_score = smatch.main(old_graphs_reentrancies, gold_graphs_reentrancies, True)[2]    
        new_smatch_score = smatch.main(new_graphs, gold_graphs, True)[2]
        new_reentr_score = smatch.main(new_graphs_reentrancies, gold_graphs_reentrancies, True)[2]
        print \
            counts, \
            "{:0.1f}".format(100 * (float(new_smatch_score) - float(old_smatch_score))), \
            "{:0.1f}".format(100 * (float(new_reentr_score) - float(old_reentr_score))),
        
    pickle.dump(new_graphs, open(args.data + '.new_graphs.p', "wb"))

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Arguments.')
    parser.add_argument('-silent', action='store_true')    
    parser.add_argument('-data', type=str, nargs='?', required=True)
    parser.add_argument('-action_type', type=str, nargs='?', required=True)
    parser.add_argument('-method', type=str, nargs='?', default='ORACLE')
    args = parser.parse_args()
    main(args)