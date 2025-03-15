import ctypes
import multiprocessing.shared_memory
import numpy as np
import pandas as pd
from more_itertools import batched
from  dataclasses import dataclass
from concurrent.futures.process import ProcessPoolExecutor
import multiprocessing
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

def fit_records(transactions: list[list], fi: dict[FrequentItem]):
    _sorted = [
        (sorted([ fi[record].index for record in frozenset(trx) if record in fi ])) for trx in transactions
    ]
    
    return [ s for s in _sorted if len(s) > 0 ]

def create_buffers(transactions: list[list[int]]):
    max_length = max( len(trx) for trx in transactions ) + 1
    shape = (len(transactions), max_length)
    trx_buf_shared = multiprocessing.shared_memory.SharedMemory(create=True, size=4 * shape[0] * shape[1])
    trx_idx_shared = multiprocessing.shared_memory.SharedMemory(create=True, size=4 * shape[0] )
    trx_ptr_shared = multiprocessing.shared_memory.SharedMemory(create=True, size=4 * shape[0] )
    print(trx_buf_shared.buf)
    trx_buf = np.ndarray(shape, dtype=np.int32, buffer=trx_buf_shared.buf)
    trx_idx = np.ndarray(shape[0], dtype=np.int32, buffer=trx_idx_shared.buf)
    trx_ptr = np.ndarray(shape[0], dtype=np.int32, buffer=trx_ptr_shared.buf)
    trx_buf[:,:] = -1

    for i, trx in enumerate(transactions):
        trx_buf[i][0:len(trx)] = trx
    
    np.copyto(trx_idx, np.arange(shape[0], dtype=np.int32, ))
    np.copyto(trx_ptr, np.zeros(shape[0], dtype=np.int32 ))
    return trx_buf, trx_idx, trx_ptr


def compute_lasagna(min_support: int, fi: dict[FrequentItem], transactions: list[list[int]]):
    transactions_len = len(transactions)

    ## list of indices to transactions
    #transaction_indices = np.arange(transactions_len, dtype=np.int32)
    ## transactions current item
    #transaction_ptrs = np.zeros(transactions_len, dtype=np.int32)
    # the root node
    transactions, transaction_indices, transaction_ptrs = create_buffers(transactions)
    print(transactions)
    root = Node(parent = Parent(),begin=0, end=len(transactions), support=len(transactions), positive=True)
    # the levels
    levels = []

    # the negative nodes
    negative_nodes = [] 

    NUM_WORKERS = 1 #multiprocessing.cpu_count()
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        for current_item in range(len(fi)):
            # the next nodes
            next_nodes = []
            # the next negative nodes
            next_negative_nodes = []
            # use root if levels is empty, then add negative nodes
            current_nodes = (levels[-1] if len(levels) > 0 else [root]) + negative_nodes

            grid = np.array_split(np.arange(len(current_nodes),dtype=np.int32), NUM_WORKERS)
            grid = [ [ (i, current_nodes[i]) for i in chunk ] for chunk in grid ]
    
            results = [
                executor.submit(lasagna_worker, current_item, nodes, transactions, transaction_indices, transaction_ptrs, transactions_len)
                for nodes in grid
            ]

            for result in results:
                positive, negative = result.result()
                next_nodes +=positive
                next_negative_nodes +=negative

            print(next_nodes, next_negative_nodes)

            #for index, node in enumerate(current_nodes):
            #    next_parent = node.parent if node.positive == False else Parent(len(levels) -1, index)
            #    positive, negative = process_node(current_item, node, transactions,transaction_indices, transaction_ptrs, transactions_len, next_parent)
            #    if positive: next_nodes.append(positive)
            #    if negative: next_nodes.append(negative)
            # write back the next level
            levels.append(next_nodes)
            # swap negative nodes list
            negative_nodes = next_negative_nodes

    return levels

def lasagna_worker(
        current_item: int,
        nodes: list[(int, Node)], 
        transactions: np.ndarray, 
        transaction_indices: np.ndarray, 
        transaction_ptrs: np.ndarray, 
        transactions_len: int):
    positive_nodes = []
    negative_nodes = []
    print(nodes,current_item, transactions, transaction_indices, transaction_ptrs)
    for i, node in nodes:
        next_parent = node.parent if node.positive == False else Parent(current_item -1, i)
        positive, negative = process_node(current_item, node, transactions,transaction_indices, transaction_ptrs, transactions_len, next_parent)
        if positive: positive_nodes.append(positive)
        if negative: negative_nodes.append(negative)
    print(nodes,current_item,positive,negative, transactions, transaction_indices, transaction_ptrs)

    return positive_nodes, negative_nodes    
    
def process_node(
        current_item: int,
        node: Node, 
        transactions: np.ndarray, 
        transaction_indices: np.ndarray, 
        transaction_ptrs: np.ndarray, 
        transactions_len: int, 
        next_parent: Parent):
    
    head, tail = [], []
    for i in range(node.begin, node.end):
        # transaction index
        tid = transaction_indices[i]
        # pointer (index) into tid transaction
        ptr = transaction_ptrs[tid]
        # the actual transaction
        trx = transactions[tid]

        # if we have not exhausted the transaction
        if trx[ptr] != -1:
            # if the elemented pointed by ptr into trx is our current_item
            if trx[ptr] == current_item:
                ptr = ptr + 1       # increment pointr
                transaction_ptrs[tid] = ptr
                head.append(tid)    # add item into head list
            else:
                tail.append(tid)
    # write back head and tail into our transaction indices list
    transaction_indices[node.begin:node.begin + len(head) + len(tail)] = head + tail

    # next parent is current node if it's a match ( True ), else the node's parent
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
    return (
        positive if positive_local_support > min_support else None,
        negative if negative_local_support > min_support else None
    )

    
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
    c_levels = 0
    c_nodes = 0
    c_counter = 0
    frequent_items = dict()
    for i, level in enumerate(levels):
        c_levels +=1
        for node in level:
            c_nodes += 1
            ancestors = get_ancestors(i, node)
            for ancestor in ancestors:
                c_counter += 1
                # key = frozenset(ancestor)
                # frequent_items[key] = (frequent_items[key] if key in frequent_items else 0) + node.support
                #frequent_items.append((node.support, new_var))
    return c_levels, c_nodes, c_counter  #pd.DataFrame(data=[ (support, itemsets) for itemsets, support in frequent_items.items()], columns=('support','itemsets'))

if __name__ == '__main__':
    import stuff
   
    transactions = stuff.load_dummy()
    min_support = .01
    header, reverse_index = extract_first(min_support, transactions)
    fitted = fit_records(transactions, header)
    levels = compute_lasagna(min_support, header, fitted)
    
    print(fitted,header)
    c_levels, c_nodes, c_counter = extract_fp(levels,header, dataset_size=len(transactions), reverse_index = reverse_index)
    print({
        'c_levels' : c_levels, 
        'c_nodes' : c_nodes, 
        'c_counter' : c_counter
    })
    for i,level in enumerate(levels):
        for leaf in level:
            print('Level {}'.format(i), leaf)
