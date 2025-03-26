import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth
if __name__ == '__main__':
    import scripts.datasets as datasets
    dataset = datasets.load_scontrini()
    te = TransactionEncoder()
    te_ary = te.fit(dataset).transform(dataset)
    df = pd.DataFrame(te_ary, columns=te.columns_)

    print(fpgrowth(df, .001, use_colnames=True))