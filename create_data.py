import pickle
import argparse
import itertools
from tqdm import tqdm
from utils import *
from graph import *

def data(args):
    counts = {}
    out_data = []
    raw_data = get_raw_data(args.data, args.parsed, args.alignments)
    data = []

    if args.data_amr != '':
        amr_data = pickle.load(open(args.data_amr, "rb"))
        for amr, raw in zip(amr_data, raw_data):
            src, tgt, sentence, alignment = raw
            tuples, dic = amr
            data.append((Graph(tuples, dic), tgt, sentence, alignment))
    else:
        data = raw_data
    
    if not args.silent:
        data_iter = tqdm(data)
    else:
        data_iter = data
    for src, tgt, sentence, alignment in data_iter:
        align_map = {}
        for tok in alignment:
            v1, v2 = tok.split('-')
            if v2 in src.nodes and v1 in tgt.nodes:
                align_map[v2] = v1    
        permutations = []
        for item in itertools.permutations(
            [x for x in src.nodes if x in align_map], 3
        ):
            permutations.append(item)
        actions = oracle(src, tgt, align_map, permutations, args.action_type)
        for key in actions:
            if key not in counts:
                counts[key] = 0
            counts[key] += len(actions[key])
        out_data.append(
            (sentence, src.smatch_relations, actions, tgt.smatch_relations)
        )
        
        # # for s2s, print input and output sequences:
        # print('IN', ' '.join(src_seq))
        # actions_seq = []
        # for a in actions['add']:
        #     actions_seq.extend([a[2], a[3], a[4]])
        # if actions_seq == []:
        #     actions_seq = ['EMPTY']
        # print('OUT', ' '.join(actions_seq))
    
    if not args.silent:
        for key in counts:
            print('Number of ' + key + ': ' + str(counts[key]))
    return out_data
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Arguments.')
    parser.add_argument('-silent', action='store_true')    
    parser.add_argument('-data', type=str, nargs='?', required=True)
    parser.add_argument('-data_amr', type=str, nargs='?', default='')
    parser.add_argument('-parsed', type=str, nargs='?', required=True)
    parser.add_argument('-alignments', type=str, nargs='?', required=True)
    parser.add_argument('-action_type', type=str, nargs='?', required=True)
    args = parser.parse_args()
    
    if not args.silent:
        print 'Creating data from:', args.data
    out_data = data(args)
    out_data_path = args.parsed + '.save.p'
    pickle.dump(out_data, open(out_data_path, "wb"))
    if not args.silent:
        print 'Length of generated dataset:', len(out_data)
        print 'Dataset saved to:', out_data_path
