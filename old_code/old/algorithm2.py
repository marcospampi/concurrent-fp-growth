from dataclasses import dataclass
import enum
from typing import Hashable, Optional, Self
import numpy as np
import pandas as pd

class PartitionType(enum.Enum):
    Root = -1
    Left = 0
    Right = 1


    

@dataclass
class Partition:
    partition_type: PartitionType
    parent: Optional[Self] = None
    index: int = 0
    depth: int = 0
    
    extents: tuple[int,int] = (0,0)
    support: float = 1.0

    label: int = -1

    def is_left(self) -> bool:
        return self.partition_type == PartitionType.Left
    def is_right(self) -> bool:
        return self.partition_type == PartitionType.Right
    def is_root(self) -> bool:
        return self.partition_type == PartitionType.Root
    def is_empty(self) -> bool:
        return self.extents[0] == self.extents[1]

@dataclass 
class FrequentOneItem:
    item: any 
    label: int
    support: float


def extract_unique_items(min_support, transactions, max_support, number_of_transactions):
    frozen_trxs = []

    unique_items: dict[Hashable,float] = dict()
    for trx in transactions:
        frozen = frozenset(trx)
        frozen_trxs.append(frozen)
        for item in frozen:
            unique_items[item] = 1 + (unique_items[item] if item in unique_items else 0)
    
    unique_items = sorted([ 
        (item, count / number_of_transactions) 
        for (item, count) in unique_items.items() 
            if min_support <= (count / number_of_transactions) <= max_support  
    ], key=lambda x: x[1], reverse=True)

    frequent_one_items = {
        item : FrequentOneItem(
            item = item,
            label = i,
            support=support
        ) for i, (item, support) in enumerate(unique_items)
    };

    
    return frequent_one_items, frozen_trxs

def fit_transactions(min_support: float,transactions: list[list[Hashable]], *,max_support:float=1.0) -> tuple[dict[Hashable, FrequentOneItem],np.ndarray,np.ndarray,np.ndarray]:
    number_of_transactions = len(transactions)

    frequent_one_items, mapped_trxs = extract_unique_items(min_support, transactions, max_support, number_of_transactions)

    mapped_trxs = [
        sorted([ frequent_one_items[i].label for i in trx if i in frequent_one_items ], reverse=True) for trx in mapped_trxs
    ]
    max_trx_size = max([ len(trx) for trx in mapped_trxs ])

    transaction_array = np.zeros((number_of_transactions, max_trx_size), dtype=np.int32)
    transactions_indices = np.arange(number_of_transactions,dtype=np.int32)
    transactions_pointers = np.zeros(number_of_transactions,dtype=np.int32)
    for i,trx in enumerate(mapped_trxs):
        current_trx_len = len(trx)
        transaction_array[i,:current_trx_len] = trx
        transactions_pointers[i] = current_trx_len - 1
    
    return (
        frequent_one_items,
        transaction_array,
        transactions_indices,
        transactions_pointers
    )
   
def process_partition(
        partition: Partition, 
        depth: int, 
        left_pad_memory: np.ndarray,
        right_pad_memory: np.ndarray,
        transaction_array: np.ndarray,
        transaction_indices: np.ndarray,
        transaction_pointers: np.ndarray
    ):
    transactions_count = transaction_array.shape[0]
    head = 0
    tail = 0
    begin, end = partition.extents

    label = depth - 1 

    for i in range(begin, end):
        tid = transaction_indices[i]
        ptr = transaction_pointers[tid]
        if ptr > -1:
            trx = transaction_array[tid]
            if trx[ptr] == label:
                left_pad_memory[head] = tid
                head+=1
                transaction_pointers[tid] = ptr - 1
            else:
                right_pad_memory[tail] = tid
                tail+=1

    left = Partition(
        parent=partition if not partition.is_right() else partition.parent,
        partition_type=PartitionType.Left,
        depth=depth, 
        support=head / transactions_count, 
        extents=(begin, begin + head),
        label=label
    )
    right = Partition(
        parent=partition if not partition.is_right() else partition.parent, 
        partition_type=PartitionType.Right,
        depth=depth, 
        support=tail / transactions_count, 
        extents=(begin + head, begin + head + tail ),
        label=(partition if not partition.is_right() else partition.parent).label
    )

    transaction_indices[begin: begin + head] = left_pad_memory[0:head]
    transaction_indices[begin + head:begin + head + tail ] = right_pad_memory[0: tail]
    return left, right     
   
def create_partitions_tree(min_support: float, transaction_array, transaction_indices, transaction_pointers, number_of_frequent_1items):
    root = Partition(extents=(0, transaction_array.shape[0]), depth=0, partition_type=PartitionType.Root)
    depths: list[list[Partition]] = [[root]]

    right_partitions: list[Partition] = []

    left_pad_memory = np.zeros(transaction_array.shape[0],dtype=np.int32)
    right_pad_memory = np.zeros(transaction_array.shape[0],dtype=np.int32)

    supports = np.zeros(number_of_frequent_1items + 1, dtype=float)

    for depth in range(1,number_of_frequent_1items+1):
        if depth == 4:
            depth = depth
        current_left_partitions: list[Partition] = []
        current_right_partitions: list[Partition] = []

        working_partitions = depths[depth-1]+right_partitions
        if len(working_partitions) == 0:
            break
            
        for partition in working_partitions:
            left, right = process_partition(partition, depth,left_pad_memory, right_pad_memory , transaction_array, transaction_indices, transaction_pointers )
            current_left_partitions.append(left)
            current_right_partitions.append(right)


        #supports[:]=0
        #for p in current_left_partitions + current_right_partitions:
        #    supports[p.depth if p.is_left() else p.parent.depth] += p.support
        #print(supports)
        #print('depth {}\tcumulative_support:{}'.format(depth, cumulative_support))
        #if cumulative_support < min_support:
        #    break
        
        left_partitions = [p for p in current_left_partitions if not p.is_empty()]
        right_partitions = [p for p in current_right_partitions if not p.is_empty()]
        
        for i in range(len(left_partitions)):
            left_partitions[i].index = i
        
        # print(f'depth {depth}:')
        # print(supports_per_depth)
        depths.append(left_partitions)

    return depths

def get_ancestors(partition: Partition):
    ancestor = partition
    ancestors = []
    while ancestor:=ancestor.parent:
        if ancestor.partition_type == PartitionType.Left:
            ancestors.append(ancestor.depth - 1)
    return ancestors

def project_at_depth(tree: list[list[Partition]], depth: int, rv1):
    itemsets: dict[frozenset, float] = dict()
    for partition in tree[depth]:
        path = []
        support = partition.support
        while partition and partition.partition_type != PartitionType.Root:
            path.append(rv1[partition.label])
            key = frozenset(path)
            itemsets[key] = support + (itemsets[key] if key in itemsets else 0.0)
            partition = partition.parent
    return itemsets

def compute_frequent_itemsets(min_support: float,transactions: list[list[Hashable]], *,max_support:float=1.0):
    frequent_one_items, transaction_array, transaction_indices, transaction_pointers = fit_transactions(min_support,transactions, max_support=max_support)
    reverse_f1i = [ item.item for item in frequent_one_items.values()]
    number_of_frequent_1items = len(frequent_one_items)

    tree = create_partitions_tree(min_support,transaction_array, transaction_indices, transaction_pointers, number_of_frequent_1items)

    
    #for item in range(number_of_frequent_1items):
    #    depth = item + 1
    #    partitions = depths[depth]
    #    local_frequent_itemsets : dict[frozenset, float] = dict()
#
    #    for partition in partitions:
    #        if partition.partition_type == PartitionType.Left:
    #            key = frozenset([item])
    #            local_frequent_itemsets[key] = partition.support + (local_frequent_itemsets[key] if key in local_frequent_itemsets else 0.0)
    #            ancestors = get_ancestors(partition)
    #            for seq in range(len(ancestors)):
    #                key = frozenset([item, *ancestors[:seq]])
    #                local_frequent_itemsets[key] = partition.support + (local_frequent_itemsets[key] if key in local_frequent_itemsets else 0.0)
    #            
    #    for itemset, support in local_frequent_itemsets.items():
    #        frequent_itemsets[itemset] = support + ( frequent_itemsets[itemset] if itemset in frequent_itemsets else 0.0)

    # 
    # for i, depth in enumerate(tree):
    #     print(f"Depth {i}")
    #     if i > 0:
    #         label = i - 1
    #         item = reverse_f1i[label]
    #         print(f"Item: {item}")
    #     for partition in depth:
    #         txt = f"""\tParent: {(partition.parent.depth, partition.parent.index) if partition.parent else None} 
    #     Type: {partition.partition_type}
    #     Extents: {partition.extents}
    #     Support: {partition.support}\n"""
    #         print(txt)
    # itemsets = []
    # for (k,s) in project_at_depth(tree,3, reverse_f1i).items():
    #     itemsets.append([s,k])

    #itemsets = []
    #for d in range(1, len(tree)):
    #    for (k,s) in project_at_depth(tree,d, reverse_f1i).items():
    #        itemsets.append([s,k])
    # df = pd.DataFrame(
    #     columns=('support', 'itemset'),
    #     data=itemsets
    # ).sort_values(by='support', ascending=False)
    # return df
    pass



if __name__ == '__main__':
    import stuff
  
  
    transactions = stuff.load_retail()
    #print(transactions)
    print(compute_frequent_itemsets(.001, transactions))

    
