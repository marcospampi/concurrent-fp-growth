import os
import concurrent.futures
from dataclasses import dataclass
from enum import Enum

from typing import Optional, Self

import numpy as np
import pandas as pd
from misc import FittedTransaction, FrequentItemPreprocessor, Transaction


@dataclass 
class FrozenNode:
    parent: Optional[Self]
    label: int
    support: float

@dataclass
class FrozenTree:
    fip: FrequentItemPreprocessor
    headers: list[list[FrozenNode]]

class FlatTreeNodeTy(Enum):
    Left = 0
    Right = 1

class FlatFPTree:
    fip: FrequentItemPreprocessor
    labels: list[list[int]]
    node_next: int
    node_types: list[int]
    node_labels: list[int]
    node_counts: list[int]
    node_parents: list[int]
    node_lefts: list[int]
    node_rights: list[int]

    def __init__(self, fip: FrequentItemPreprocessor):
        self.fip = fip
        self.labels = []
        self.node_next: int = 0
        self.node_types = []
        self.node_labels = []
        self.node_counts = []
        self.node_parents = []
        self.node_lefts = []
        self.node_rights = []
        for label in range(fip.number_of_frequent_one_items):
            self.labels.append([])
            self.create_left(label, parent = -1)
        
    def create_node(self, ty: FlatTreeNodeTy,*, label: Optional[int] = None, parent: int = -1):
        i = self.node_next
        self.node_types.append(ty)
        self.node_counts.append(0)
        self.node_parents.append(parent)
        self.node_lefts.append(-1)
        self.node_rights.append(-1)
        self.node_next = i + 1
        if label is not None:
            self.node_labels.append(label)
            self.labels[label].append(i)
        else:
            self.node_labels.append(-1)
        return i
    def counts(self, node: int) -> int:
        return self.node_counts[node]
    def right(self, node: int) -> int:
        return self.node_rights[node]
    def left(self, node: int) -> int:
        return self.node_lefts[node]
    def parent(self, node: int) -> int:
        return self.node_parents[node]
    def label(self, node: int) -> int:
        return self.node_labels[node]
    
    def set_right(self, node: int, right: int) -> None:
        self.node_rights[node] = right
    def set_left(self, node: int, left: int) -> None:
        self.node_lefts[node] = left
    def set_parent(self, node: int, parent: int) -> None:
        self.node_parents[node] = parent
    def set_label(self, node: int, label: int) -> None:
        self.node_labels[node] = label
    def use(self, node: int, uses: int = 1) -> None:
        self.node_counts[node] += uses
    
    def create_left(self, label: int, parent: int):
        return self.create_node(FlatTreeNodeTy.Left, label = label, parent = parent )
    
    # crea e/o cammina il percorso per andare da un nodo con etichetta source a etichetta dest
    def traverse(self, node: int, source_label: int, destination_label: int,*, parent: Optional[int] = None):
        # destination is next item
        if source_label + 1 == destination_label:
            return self.traverse_left(node, destination_label, parent)
        else:
            right_destination_label = destination_label - 1
            right = self.right(node)
            if right < 0:
                right = self.create_right(right_destination_label, parent)
                self.set_right(node, right)
                return self.traverse_left(right, destination_label, parent = parent)
            else:
                label = self.label(right)
                if label > right_destination_label:
                    # create next node
                    self.split_right_edge(node,right, label, right_destination_label)

                    return self.traverse_left(right, destination_label, parent=parent)
                # label < right_destination_label
                else:
                    while self.right(right) > 0 and self.label(self.right(right)) < right_destination_label:
                        right = self.right(right)
                        label = self.label(right)
                    return self.traverse(right, label, destination_label, parent=node)
    

    def split_right_edge(self, node: int,right: int, label: int, right_label: int):

        next = self.create_right(label, self.parent(node))
        self.set_left(next, self.left(right))
        self.set_right(next, self.right(right))
        
        self.set_left(right, -1)
        self.set_right(right, next)
        
        self.set_label(right, right_label)

    def traverse_left(self, node, destination_label, parent: Optional[int] = None):
        parent = parent if parent > -1 else node
        left = self.left(node)
        if left < 0:
            left = self.create_left(destination_label, parent)
            self.set_left(node, left)
        return left

    def create_right(self,label: int, parent: int):
        return self.create_node(FlatTreeNodeTy.Right, parent = parent, label = label )
    
    def add_transaction(self, transaction: Transaction):
        trx = self.fip.transform(transaction)
        if len(trx) < 1: return
        # print("adding transaction", self.fip.to_items(trx))
        self.__add_fitted_transaction(trx)
     
    def __add_fitted_transaction(self, trx: FittedTransaction,*, count = 1):
        node = self.labels[trx[0]][0]
        
        self.use(node, count)

        for label in trx[1:]:
            node = self.traverse(node, self.label(node), label, parent = node)
            self.use(node, count)

    def __extract_upwords_path(self, node: int, include = False):
        parent = self.parent(node)
        visited = [self.label(node)] if include else []
        while parent > -1:
            visited.append(self.label(parent))
            parent = self.parent(parent)
        return list(reversed(visited))

    def project_tree(self, label: int):
        projected = FlatFPTree(self.fip)
        for node in self.labels[label]:
            support = self.counts(node)
            trx = self.__extract_upwords_path(node)
            if len(trx) > 0:
                projected.__add_fitted_transaction(trx, count = support )
        projected.__prune_less_than_minsup_nodes()
        itemsets = projected.__projected_extract_itemsets(label)
        return itemsets

    def __projected_extract_itemsets(self, label: int):
        scale = self.fip.transactions_scale
        itemsets = [
            (self.fip.frequent_one_items[label].support,frozenset({label}))
        ]
        for nodes in self.labels:
            for node in nodes:
                prefix = self.__extract_upwords_path(node, include=True)
                support = self.counts(node)
                itemsets.append((support * scale,frozenset([label,*prefix])))
        return itemsets

    def __prune_zero_support_nodes(self):
        self.labels = [
            [ node for node in nodes if self.node_counts[node] > 0] for nodes in self.labels
        ]

    def __prune_less_than_minsup_nodes(self):
        scale = self.fip.transactions_scale
        min_support = self.fip.min_support
        self.labels = [
            [ node for node in nodes if self.counts(node) * scale > min_support] for nodes in self.labels
        ]
    
    def extract_itemsets(self, max_workers: int):
        self.__prune_zero_support_nodes()
        itemsets = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=init_worker, initargs=tuple([self])) as executor:




            labels = np.arange(self.fip.number_of_frequent_one_items)
            np.random.shuffle(labels)
            grid = np.array_split(labels,max_workers)

            futures = {
                executor.submit(run_in_worker, list(labels))
                for labels in grid
            }
            for fut in concurrent.futures.as_completed(futures):
                result = fut.result()
                itemsets += (result)
                
        return itemsets
def init_worker(tree_: FlatFPTree):
    global tree
    tree = tree_
def run_in_worker(labels: list[int]):
    global tree
    result = []
    for label in labels:
        result += tree.project_tree(label)
    return result

def fpgrowth(min_support: float, dataset: list[Transaction], max_workers = None):
    max_workers = os.cpu_count() if max_workers is None else max_workers

    fip = FrequentItemPreprocessor(min_support)
    fip.fit(dataset)
    tree = FlatFPTree(fip)
    
    for trx in dataset:
        tree.add_transaction(trx)

    frequent_itemsets = tree.extract_itemsets(max_workers)
    
    df = pd.DataFrame(data=frequent_itemsets, columns=('support', 'itemsets'))
    df['itemsets'] = df['itemsets'].apply(lambda x: frozenset(fip.to_items(x)))
    return df


if __name__ == '__main__':
    import stuff
    dataset = stuff.load_T40I10D100K()
    
    result = fpgrowth(.001, dataset)
    print(result)

