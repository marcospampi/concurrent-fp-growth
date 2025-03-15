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
    support: float
    positive: bool

    def __hash__(self):
        return hash((self.parent.level, self.parent.index, self.begin, self.end, self.support))

def extract_first(min_support: int, transactions: list[list]):
    transactions_len = len(transactions)
    firsts_support = dict()
    for record in transactions:
        record_set = frozenset(record)
        for item in record_set:
            firsts_support[item] = 1 + (firsts_support[item] if item in firsts_support else 0)
    ordered = sorted([ (k,v) for k,v in firsts_support.items()], key = lambda x: x[1], reverse=True)
    frequent_items = {
        key: FrequentItem(label=key, index=index, support=support / transactions_len) for index, (key, support) in enumerate(ordered)
            if support /transactions_len>= min_support
    }
    reverse_index = [ k for k,v in ordered ]
    return frequent_items, reverse_index

def sort_records(transactions: list[list], fi: dict[FrequentItem]):
    _sorted = [
        (sorted([ fi[record].index for record in frozenset(trx) if record in fi ])) for trx in transactions
    ]
    return [ s for s in _sorted if len(s) > 0 ]

def compute_lasagna(min_support: int, fi: dict[FrequentItem], transactions: list[list[int]]):

    # list of indices to transactions
    transaction_indices = list(range(len(transactions)))
    # transactions current item
    transaction_ptrs = [0] * len(transactions)
    # the root node
    root = Node(parent = Parent(),begin=0, end=len(transactions), support=len(transactions), positive=True)
    # the levels
    levels = []

    # the negative nodes
    negative_nodes = [] 

    transactions_len = len(transactions)

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
            next_parent = node.parent if node.positive == False else Parent(len(levels) -1, index)
            # the positive node
            positive_local_support = len(head) / (-node.begin + node.end)
            negative_local_support = len(tail) / (-node.begin + node.end)

            positive = Node(
                parent=next_parent,
                begin=node.begin,
                end=node.begin + len(head),
                support=len(head) / transactions_len,
                positive=True
            )
            # the negative node
            negative = Node(
                parent= next_parent,
                begin= node.begin + len(head),
                end= node.begin + len(head) + len(tail),
                support= len(tail) / transactions_len,
                positive=False
            )

            if positive_local_support > min_support:
                next_nodes.append(positive)
            if negative_local_support > min_support:
                next_negative_nodes.append(negative)

        # write back the next level
        levels.append(next_nodes)
        # swap negative nodes list
        negative_nodes = next_negative_nodes

    return levels

def extract_fp(levels: list[list[Node]], header: dict[FrequentItem],*, dataset_size: float = 1.0, reverse_index: list[any] = None ):
    def get_ancestors(level: int,node: Node):
        ancestors = [[reverse_index[level]]]
        while True:
            level, index = node.parent.level, node.parent.index
            if not level > -1:
                break
            ancestors.append([*ancestors[-1],reverse_index[level] ])
            node = levels[level][index]

        return ancestors
    frequent_items = []
    for i, level in enumerate(levels):
        for node in level:
            ancestors = get_ancestors(i, node)
            for ancestor in ancestors:
                frequent_items.append((node.support, frozenset(ancestor)))
    return pd.DataFrame(data=frequent_items, columns=('support','itemsets'))

if __name__ == '__main__':
    from stuff import load_T10I4D100K, load_T40I10D100K, load_retail
    #transactions = [['Milk', 'Onion', 'Nutmeg', 'Kidney Beans', 'Eggs', 'Yogurt'],
    #       ['Dill', 'Onion', 'Nutmeg', 'Kidney Beans', 'Eggs', 'Yogurt'],
    #       ['Milk', 'Apple', 'Kidney Beans', 'Eggs'],
    #       ['Milk', 'Unicorn', 'Corn', 'Kidney Beans', 'Yogurt'],
    #       ['Corn', 'Onion', 'Onion', 'Kidney Beans', 'Ice cream', 'Eggs']]
    transactions = load_retail()
    min_support = .01
    header, reverse_index = extract_first(min_support, transactions)
    sorted = sort_records(transactions, header)
    levels = compute_lasagna(min_support, header, sorted)
    
    print(header)
    #print(extract_fp(levels,header, dataset_size=len(transactions), reverse_index = reverse_index).to_string())
    #for i,level in enumerate(levels):
    #    for leaf in level:
    #        print('Level {}'.format(i), leaf)
