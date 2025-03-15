def load_T10I4D100K():
    file = "../datasets/transactional_T10I4D100K.csv"
    transactions = []
    with open(file, 'r') as file:
        for line in file:
            trx = [ int(x) for x in line.split(',') if x.isnumeric() ]
            if len(trx) > 0:
                transactions.append(trx)
    return transactions

def load_T40I10D100K():
    file = "../datasets/T40I10D100K.dat"
    transactions = []
    with open(file, 'r') as file:
        for line in file:
            trx = [ int(x) for x in line.split(' ') if x.isnumeric() ]
            if len(trx) > 0:
                transactions.append(trx)
    return transactions

def load_retail():
    file = "../datasets/retail.dat"
    transactions = []
    with open(file, 'r') as file:
        for line in file:
            trx = [ int(x) for x in line.split(' ') if x.isnumeric() ]
            if len(trx) > 0:
                transactions.append(trx)
    return transactions