
from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import Generic, Literal, Optional, Self, TypeVar

import numpy as np
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

                    return self.traverse_left(right, destination_label)
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
        parent = parent if parent else node
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
        print("adding transaction {}", self.fip.to_items(trx))
        self.add_fitted_transaction(trx)
     
    def add_fitted_transaction(self, trx: FittedTransaction,*, count = 1):
        node = self.labels[trx[0]][0]
        
        self.use(node, count)

        for label in trx[1:]:
            node = self.traverse(node, self.label(node), label, parent = node)
            self.use(node, count)

    def extract_upwords_path(self, node: int):
        parent = self.parent(node)
        visited = [self.label(node)]
        while parent > -1:
            visited.append(self.label(parent))
            parent = self.parent(parent)
        return list(reversed(visited))

    def project(self, label: int):
        tree = FlatFPTree(self.fip)
        for node in self.labels[label]:
            support = self.counts(node)
            trx = self.extract_upwords_path(node)
            
            if len(trx) > 0:
                print(self.fip.to_items(trx))
                tree.add_fitted_transaction(trx, count = support )
        #tree.prune_and_seal()
        return tree, []


    def prune_and_seal(self):
        # return None
        self.node_rights = None
        self.node_lefts = None
        self.node_types = None
        self.labels = [
            [ node for node in nodes if self.node_counts[node] > 0] for nodes in self.labels
        ]
        return None

    def extract_patterns(self):
        for label in reversed(list(range(0, self.fip.number_of_frequent_one_items))):
            print(self.fip.to_item(label))
            projection = self

            depth = label
            transactions = []
            while depth > 0:
                max_label = 0
                projection, transactions_ = projection.project(depth)
                for (trx, counts) in transactions_:
                    support = counts / self.fip.transactions_count
                    if len(trx) > 0 :
                        max_label = max(max_label, trx[-1])
                        # if support >= self.fip.min_support:
                        transactions.append((trx, support))
                depth = max_label
                print([(self.fip.to_items(trx), sup) for trx,sup in transactions_])
                
        pass

def create_tree(min_support: float, dataset: list[Transaction]):
    fip = FrequentItemPreprocessor(min_support)
    fip.fit(dataset)
    tree = FlatFPTree(fip)
    
    for trx in dataset:
        tree.add_transaction(trx)
    print(tree.node_next)
    #extract_patterns(flat_tree)

    tree.prune_and_seal()
    patterns = tree.extract_patterns()
    return patterns


if __name__ == '__main__':
    import stuff
    dataset = stuff.load_pippo()
    
    tree_ = create_tree(3/len(dataset), dataset)

