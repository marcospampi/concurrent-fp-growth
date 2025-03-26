import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori
if __name__ == '__main__':
    import datasets as datasets
    dataset = datasets.load_scontrini()
    te = TransactionEncoder()
    te_ary = te.fit(dataset).transform(dataset)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    result = apriori(df, .001, use_colnames=True, low_memory=True)
    print(result)
    print(result['support'].max())