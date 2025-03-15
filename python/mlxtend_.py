import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth
if __name__ == '__main__':
    from stuff import load_T10I4D100K, load_T40I10D100K, load_retail
    dataset = load_retail()
    te = TransactionEncoder()
    te_ary = te.fit(dataset).transform(dataset)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    fpgrowth(df, .01, use_colnames=True)