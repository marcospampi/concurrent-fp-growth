import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth
if __name__ == '__main__':
    import stuff
    dataset = stuff.load_T10I4D100K()
    te = TransactionEncoder()
    te_ary = te.fit(dataset).transform(dataset)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    fpgrowth(df, .002, use_colnames=True)