import os
import concurrent.futures
from dataclasses import dataclass
from enum import Enum

from typing import Optional, Self

import numpy as np
import pandas as pd
from .FrequentItemPreprocessor import FittedTransaction, FrequentItemPreprocessor, Transaction


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
    node_supports: list[int]
    node_parents: list[int]
    node_lefts: list[int]
    node_rights: list[int]

    def __init__(self, fip: FrequentItemPreprocessor):
        self.fip = fip
        self.labels = []
        self.node_next: int = 0
        self.node_types = []
        self.node_labels = []
        self.node_supports = []
        self.node_parents = []
        self.node_lefts = []
        self.node_rights = []
        for label in range(fip.number_of_frequent_one_items):
            self.labels.append([])
            self.create_left(label, parent = -1)
        
    def create_node(self, ty: FlatTreeNodeTy,*, label: Optional[int] = None, parent: int = -1):
        i = self.node_next
        self.node_types.append(ty)
        self.node_supports.append(0)
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
    def support(self, node: int) -> int:
        return self.node_supports[node]
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
        self.node_supports[node] += uses
    
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
    
    def add_transaction(self, transaction: Transaction, count: int = 1):
        trx = self.fip.transform(transaction)
        if len(trx) < 1: return
        # print("adding transaction", self.fip.to_items(trx))
        #print("Adding transaction", (self.fip.to_items(trx), count))
        self.__add_fitted_transaction(trx, count=count)
     
    def __add_fitted_transaction(self, trx: FittedTransaction,*, count = 1):
        node = self.labels[trx[0]][0]
        
        self.use(node, count)

        for label in trx[1:]:
            node = self.traverse(node, self.label(node), label, parent = node)
            self.use(node, count)

    def __extract_path_from_node(self, node: int, include = False):
        parent = self.parent(node)
        visited = [self.label(node)] if include else []
        while parent > -1:
            visited.append(self.label(parent))
            parent = self.parent(parent)
        return list(reversed(visited))

    def __extract_paths_from_label(self, label):
        paths: list[tuple[list], int] = []
        for node in self.labels[label][1:]:
            path = self.__extract_path_from_node(node)
            support = self.support(node)
            if support > 0: paths.append((support, path))
        return paths
    
    def project_and_mine_tree(self, label: int):
        #print("Current label:" + str(self.fip.to_item(label)))
        paths = self.__extract_paths_from_label(label)
        #print("Computed paths:", paths)
        paths_len = len(paths)

        itemsets = [
            (self.fip.frequent_one_items[label].support, [label])
        ]
        if paths_len == 1:
            support, path = paths[0]
            itemsets.append(
                (support, path + [label])
            )
        elif len(paths) > 1:
            fip, tree = self.__project_tree(paths)
            for sup, path in tree.__extract_itemsets():
                itemsets.append((sup, fip.to_items(path) + [label]))
        
        #print("Found itemsets: ",[(self.fip.to_items(path), supp) for supp, path in itemsets])
        
        return itemsets

    def __project_tree(self, paths):
        fip = FrequentItemPreprocessor(self.fip.min_support)
        fip.fit([item for _, item in paths], [support for support, _ in paths])
        tree = FlatFPTree(fip)
        for support, trx in paths:
            tree.add_transaction(trx, support)
        return fip,tree
        ##fip = FrequentItemPreprocessor(min_support=0)
        ##paths = []
        ##counts = []
        ##for node in self.labels[label][1:]:
        ##    trx = self.__extract_upwords_path(node)
        ##    count = self.support(node)
        ##    if len(trx) > 0:
        ##        paths.append(trx)
        ##        counts.append(count)
        ##
        ##if len(paths) > 0:
        ##    print('paths', paths)
        ##    fip.fit(paths)
        ##    tree = FlatFPTree(fip)
        ##    for trx, count in zip(paths, counts):
        ##        print(trx, count)
        ##        tree.__add_fitted_transaction(fip.transform(trx), count=count)
        ##    #tree.__prune_less_than_minsup_nodes()
        ##    
        ##    for labels in (tree.labels):
        ##        for node in labels:
        ##            
        ##            prefix = sorted(fip.to_items(tree.__extract_upwords_path(node, True)))
        ##            print(self.fip.to_items(prefix + [label]), tree.support(node))
        ##    return []
        ##return []

    def __projected_extract_itemsets(self, label: int):
        scale = self.fip.transactions_scale
        itemsets = [
            (self.fip.frequent_one_items[label].support,frozenset({label}))
        ]
        for nodes in self.labels:
            for node in nodes:
                prefix = self.__extract_path_from_node(node, include=True)
                support = self.support(node)
                itemsets.append((support * scale,frozenset([label,*prefix])))
        return itemsets

    def __prune_zero_support_nodes(self):
        self.labels = [
            [ node for node in nodes if self.node_supports[node] > 0] for nodes in self.labels
        ]

    def __prune_less_than_minsup_nodes(self):
        min_support = self.fip.min_support
        self.labels = [
            [ node for node in nodes if self.support(node) > min_support] for nodes in self.labels
        ]
    
    def extract_itemsets(self, max_workers: int):
        # self.__prune_zero_support_nodes()

        if max_workers > 0:
            return self.__extract_itemsets_mp(max_workers)
        else:
            return self.__extract_itemsets()

    def __extract_itemsets(self):
        itemsets = []
        for label in range(self.fip.number_of_frequent_one_items):
            itemsets += self.project_and_mine_tree(label)
        return itemsets
    def __extract_itemsets_mp(self, max_workers: int):
        itemsets = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers, initializer=mp_init_worker, initargs=tuple([self])) as executor:
            labels = np.arange(self.fip.number_of_frequent_one_items)
            np.random.shuffle(labels)
            grid = np.array_split(labels,max_workers)
            futures = {
                executor.submit(mp_run, list(labels))
                for labels in grid
            }
            for fut in concurrent.futures.as_completed(futures):
                result = fut.result()
                itemsets += (result)
        return itemsets

def mp_init_worker(tree_: FlatFPTree):
    global tree
    tree = tree_
def mp_run(labels: list[int]):
    global tree
    result = []
    for label in labels:
        result += tree.project_and_mine_tree(label)
    return result

