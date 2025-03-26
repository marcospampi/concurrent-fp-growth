
from dataclasses import dataclass
from enum import Enum
from time import sleep
from typing import Optional, Self
from misc import FrequentItemPreprocessor, Transaction
import gc
class NodeType(Enum):
    Left = 0
    Right = 1

@dataclass
class Node:
    type: NodeType
    label: int = -1
    support: int = 0
    parent: Optional[Self] = None
    left: Optional[Self] = None
    right: Optional[Self] = None

    def is_left(self):
        return self.type == NodeType.Left
    def is_right(self):
        return self.type == NodeType.Left
    forward_index: int = -1

@dataclass 
class FrozenNode:
    parent: Optional[Self]
    label: int
    support: float

@dataclass
class FrozenTree:
    fip: FrequentItemPreprocessor
    headers: list[list[FrozenNode]]
    


class Tree:
    fip: FrequentItemPreprocessor
    headers: list[list[Node]]
    nodes = list[Node]
    def __init__(self, fip: FrequentItemPreprocessor):
        self.fip = fip
        self.headers = [ 
            [Node(type=NodeType.Left, label=i)] 
            for i in range(len(fip.frequent_one_items))
        ]
    
    def add_transaction(self, trx: Transaction):
        trx = self.fip.transform(trx)
        trx_size = len(trx)
        
        if trx_size == 0:
            return

        j = trx[0]
        node: Node = self.headers[j][0]
        node.support+=1
        last_parent = node
        i = 1
        j = j + 1
        while node and i < trx_size:
            
            if j == trx[i]:
                if not node.left:
                    node.left = Node(type=NodeType.Left, parent=last_parent, label = j)
                    self.headers[j].append(node.left)
                
                node.left.support += 1
                last_parent = node.left
                node = node.left
                i+=1
            else:
                if not node.right:
                    node.right = Node(type=NodeType.Right, parent=last_parent )
                node = node.right

            j+=1
    def finalize(self):
        for header in self.headers:
            for i, node in enumerate(header):
                node.forward_index = i
        headers = [[]] * len(self.headers)
        for i, header in enumerate(self.headers):
            for node in header:
                parent = headers[node.parent.label][node.parent.forward_index] if node.parent else None
                next = FrozenNode(parent=parent, support=node.support / self.fip.transactions_count,label=node.label)
                headers[i].append(next)
        return FrozenTree(self.fip, headers)
                 

def create_tree(min_support: float, dataset: list[Transaction]):
    fip = FrequentItemPreprocessor(min_support)
    fip.fit(dataset)
    tree = Tree(fip)
    for trx in dataset:
        tree.add_transaction(trx)
    return tree.finalize()


if __name__ == '__main__':
    import stuff
    dataset = stuff.load_scontrini()
    
    tree = create_tree(.001, dataset)

