import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth
if __name__ == '__main__':
    file = "/home/marco/Scrivania/uni/datamining/lab-data-mining/progetto/transactional_T10I4D100K.csv"
    dataset = []
    with open(file, 'r') as file:
        for line in file:
            trx = list(map(lambda x: int(x), line.split(',')))
            if len(trx) > 0:
                dataset.append(trx)


    te = TransactionEncoder()
    te_ary = te.fit(dataset).transform(dataset)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    print(fpgrowth(df, .01, use_colnames=True).to_string())