from src.FlatFPTree import FlatFPTree
from src.FrequentItemPreprocessor import FrequentItemPreprocessor, Transaction, FittedTransaction


import pandas as pd


import os


def fpgrowth_mp(min_support: float, dataset: list[Transaction], max_workers = None) -> pd.DataFrame:
    max_workers = os.cpu_count() if max_workers is None else max_workers

    dataset_len = len(dataset)
    
    # convert min_support to integer
    integer_min_support = int(dataset_len * min_support)
    
    # preprocess the data
    fip = FrequentItemPreprocessor(integer_min_support)
    fip.fit(dataset)
    
    # create the tree object
    tree = FlatFPTree(fip)

    # add transactions
    for trx in dataset:
        tree.add_transaction(trx)

    # add itemsets
    frequent_itemsets = tree.extract_itemsets(max_workers)

    # fit collected itemsets into a pandas' DataFrame
    df = pd.DataFrame(data=frequent_itemsets, columns=('support', 'itemsets'))
    df['itemsets'] = df['itemsets'].apply(lambda trx: frozenset(fip.to_items(trx)))
    df['support'] = df['support'].apply(lambda x: x / dataset_len)
    df = df[df['support'] >= min_support]
    return df

def fpgrowth(min_support: float, dataset: list[Transaction]) -> pd.DataFrame:
    return fpgrowth_mp(min_support, dataset, max_workers=0)
