from collections import OrderedDict
from dataclasses import dataclass
from typing import Hashable, Sequence


@dataclass 
class FrequentOneItem:
    item: Hashable 
    label: int
    support: float

type Transaction = list[Hashable]
type FittedTransaction = list[int]

class FrequentItemPreprocessor:
    min_support: float
    max_support: float
    transactions_scale: float
    transactions_count: int
    number_of_frequent_one_items: int
    frequent_one_items: list[FrequentOneItem]
    frequent_one_items_map: dict[Hashable, int]
    
    def __init__(self,min_support: float,*, max_support = 1.0):
        self.min_support = min_support
        self.max_support = max_support
    
    def fit(self, transactions: Sequence[Transaction]):
        transactions_count: int = 0

        frequent_one_item_supports: dict[Hashable, int] = dict()
        for trx in transactions:
            transactions_count += 1
            for item in frozenset(trx):
                frequent_one_item_supports[item] = 1 + (frequent_one_item_supports[item] if item in frequent_one_item_supports else 0)
        #frequent_one_item_supports = {key: (count / transactions_count) for key, count in frequent_one_item_supports.items()}
        self.frequent_one_items = sorted([
            FrequentOneItem(
                item = item,
                label = -1,
                support=count / transactions_count
            ) 
            for ( item, count ) in frequent_one_item_supports.items()
                if  self.min_support <= (count / transactions_count) <= self.max_support 
        ], reverse=True, key = lambda foi: (foi.support , foi.item) )
        
        self.frequent_one_items_map = dict()

        for label in range(len(self.frequent_one_items)):
            item_ref = self.frequent_one_items[label]
            item_ref.label = label
            self.frequent_one_items_map[item_ref.item] = label
        self.transactions_count = transactions_count
        self.transactions_scale = 1 / transactions_count
        self.number_of_frequent_one_items = len(self.frequent_one_items)
    
    def transform(self, transaction: Transaction) -> FittedTransaction:
        return sorted([ self.frequent_one_items_map[item] for item in frozenset(transaction) if item in self.frequent_one_items_map])

    def fit_transform(self, transactions: Sequence[Transaction]):
        self.fit(transactions)
        return [ self.transform(trx) for trx in transactions ]
    
    def to_item(self, label: int):
        return self.frequent_one_items[label].item
    
    def to_items(self, labels: list[int]):
        return [ self.to_item(label) for label in labels]