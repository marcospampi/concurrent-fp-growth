from src.FlatFPTree import FlatFPTree
from src.FrequentItemPreprocessor import FrequentItemPreprocessor, Transaction, FittedTransaction


import pandas as pd


import os


def fpgrowth_mp(min_support: float, dataset: list[Transaction], max_workers = None) -> pd.DataFrame:
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

def fpgrowth(min_support: float, dataset: list[Transaction]) -> pd.DataFrame:
    return fpgrowth_mp(min_support, dataset, max_workers=0)

# if __name__ == '__main__':
#     import scripts.datasets as datasets
#     dataset = datasets.load_scontrini()
#     
#     result = fpgrowth_mp(.001, dataset)
#     print(result)
