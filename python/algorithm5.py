from typing import Optional
from python.misc import FrequentItemPreprocessor


type NodeType = int
type LabelType = int

class FPTree:
  node_next: NodeType
  labels: list[list[NodeType]]
  node_edges: list[dict[LabelType,NodeType]]
  node_supports: list[int]
  node_parents: list[NodeType]
  fip: FrequentItemPreprocessor
  def __init__(self, fip: FrequentItemPreprocessor):
    self.node_next = 0
    self.node_edges = []
    self.node_supports = []
    self.fip = fip
    self.labels = [
      [ self.create_node(label) ] for label in range(fip.number_of_frequent_one_items)
    ]

  def create_node(self, label: int, parent: int = -1 ):
    node = self.__advance_node_counter()
    self.node_edges.append(dict())
    self.node_parents.append(parent)
    self.node_supports.append(0)
    self.labels[label].append(node)

    return node

  def __advance_node_counter(self):
      node = self.node_next
      self.node_next = node + 1
      return node
  

