from typing import Optional
import pandas as pd
from  dataclasses import dataclass

@dataclass
class FrequentItem:
    label: any
    index: int
    support: int

@dataclass
class Parent:
    level: int = -1
    index: int = -1

@dataclass
class Node:
    parent: Parent
    begin: int
    end: int
    support: int
    type: bool
    prefix: Optional[tuple]

    def __hash__(self):
        return hash((self.parent.level, self.parent.index, self.begin, self.end, self.support))

def extract_first(min_support: int, transactions: list[list]):
    firsts_support = dict()
    for record in transactions:
        record_set = set(record)
        for item in record_set:
            firsts_support[item] = 1 + (firsts_support[item] if item in firsts_support else 0)
    ordered = sorted([ (k,v) for k,v in firsts_support.items()], key = lambda x: x[1], reverse=True)
    frequent_items = {
        key: FrequentItem(label=key, index=index, support=support) for index, (key, support) in enumerate(ordered)
            if support >= min_support
    }
    reverse_index = [ k for k,v in ordered ]
    return frequent_items, reverse_index

def sort_records(transactions: list[list], fi: dict[FrequentItem]):
    _sorted = [
        sorted([ fi[record].index for record in trx if record in fi ]) for trx in transactions
    ]
    return [ s for s in _sorted if len(s) > 0 ]

def compute_lasagna(min_support: int, fi: dict[FrequentItem], transactions: list[list[int]]):

    # list of indices to transactions
    transaction_indices = list(range(len(transactions)))
    # transactions current item
    transaction_ptrs = [0] * len(transactions)
    # the root node
    root = Node(parent = Parent(),begin=0, end=len(transactions), support=len(transactions), type=True, prefix=None)
    # the levels
    levels = []
    
    # the negative nodes
    negative_nodes = [] 

    for current_item in range(len(fi)):

        # the next nodes
        next_nodes = []
        # the next negative nodes 
        next_negative_nodes = []
        # use root if levels is empty, then add negative nodes
        current_nodes = (levels[-1] if len(levels) > 0 else [root]) + negative_nodes
        for index, node in enumerate(current_nodes):
            head, tail = [], []
            for i in range(node.begin, node.end):
                # transaction index
                tid = transaction_indices[i]
                # pointer (index) into tid transaction
                ptr = transaction_ptrs[tid]
                # the actual transaction
                trx = transactions[tid]
                
                # if we have not exhausted the transaction
                if ptr != -1:
                    # if the elemented pointed by ptr into trx is our current_item
                    if trx[ptr] == current_item:
                        head.append(tid)    # add item into head list
                        ptr = ptr + 1       # increment pointr

                        # write back update, put -1 if exhausted
                        transaction_ptrs[tid] = ptr if ptr < len(trx) else -1
                    else:
                        tail.append(tid)
            # write back head and tail into our transaction indices list
            transaction_indices[node.begin:node.begin + len(head) + len(tail)] = head + tail
            
            # next parent is current node if it's a match ( True ), else the node's parent
            next_parent = node.parent if node.type == False else Parent(len(levels) -1, index)
            # the positive node
            positive = Node(next_parent, node.begin, node.begin + len(head), len(head), type=True, prefix=None)
            # the negative node
            negative = Node(next_parent, node.begin + len(head), node.begin + len(head) + len(tail), len(tail), type=False, prefix=None)

            if positive.support >= min_support:
                next_nodes.append(positive)
            if negative.support >= min_support:
                next_negative_nodes.append(negative)

        # write back the next level
        levels.append(next_nodes)
        # swap negative nodes list
        negative_nodes = next_negative_nodes

    return levels

def extract_fp(levels: list,*, dataset_size: float = 1.0, reverse_index: list[any] = None ):
    item_sets = []
    visited = set()

    def visit(level: int, node: Node):
        name = level if reverse_index is None else reverse_index[level]
        if node not in visited:
            visited.add(node)
            if node.parent.level > 0:
                parent = levels[node.parent.level][node.parent.index]
                visit(node.parent.level, parent)
                node.prefix = frozenset([*parent.prefix,name])
            else:
                node.prefix = frozenset([name])
            
            item_sets.append((float(node.support) / dataset_size, node.prefix))
    
    for level, nodes in reversed(list(enumerate(levels))):
        for node in nodes:
            visit(level, node)
    return pd.DataFrame(data=item_sets, columns=('support', 'itemsets'))

if __name__ == '__main__':
    file = "/home/marco/Scrivania/uni/datamining/lab-data-mining/progetto/transactional_T10I4D100K.csv"
    transactions = []
    with open(file, 'r') as file:
        for line in file:
            trx = list(map(lambda x: int(x), line.split(',')))
            if len(trx) > 0:
                transactions.append(trx)
    min_support = int(.01 * len(transactions)) 
    f1i, reverse_index = extract_first(min_support, transactions)
    sorted = sort_records(transactions, f1i)
    levels = compute_lasagna(min_support, f1i, sorted)
    
    print(extract_fp(levels, dataset_size=len(transactions), reverse_index = reverse_index).to_string())
    print(sum([len(level) for level in levels]))
    # for i,level in enumerate(levels):
    #     for leaf in level:
    #         print('Level {}'.format(i), leaf)
