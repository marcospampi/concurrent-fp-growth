from  dataclasses import dataclass

@dataclass
class FrequentItem:
    label: any
    index: int
    support: int

@dataclass
class Level:
    parent: int
    begin: int
    end: int
    support: int
    type: bool

def extract_first(min_support: int, transactions: list[list]):
    firsts_support = dict()
    for record in transactions:
        record_set = set(record)
        for item in record_set:
            firsts_support[item] = 1 + (firsts_support[item] if item in firsts_support else 0)
    ordered = sorted([ (k,v) for k,v in firsts_support.items()], key = lambda x: x[1], reverse=True)
    return {
        key: FrequentItem(label=key, index=index, support=support) for index, (key, support) in enumerate(ordered)
            if support >= min_support
    }

def sort_records(transactions: list[list], fi: dict[FrequentItem]):
    _sorted = [
        sorted([ fi[record].index for record in trx if record in fi ]) for trx in transactions
    ]
    return [ s for s in _sorted if len(s) > 0]

def compute_lasagna(min_support: int, fi: dict[FrequentItem], transactions: list[list[int]]):
    to_transaction_ptr = [0] * len(transactions)
    levels = [[Level(parent = -1,begin=0, end=len(transactions), support=len(transactions), type=True)]]
    to_transaction = list(range(len(transactions)))

    
    for current_item in range(len(fi)):
        next_levels = []
        for parent, level in enumerate(levels[-1]):
            head, tail = [], []
            for i in range(level.begin, level.end):
                tid = to_transaction[i]
                ptr = to_transaction_ptr[tid]
                trx = transactions[tid]
                if ptr != -1:
                    if trx[ptr] == current_item:
                        head.append(tid)
                        ptr = ptr + 1
                        to_transaction_ptr[tid] = ptr if ptr < len(trx) else -1
                    else:
                        tail.append(tid)
            to_transaction[level.begin:level.begin + len(head) + len(tail)] = head + tail
            
            positive = Level(parent, level.begin, level.begin + len(head), len(head), type=True)
            negative = Level(parent, level.begin + len(head), level.begin + len(head) + len(tail), len(tail), type=False)

            if positive.support >= min_support:
                next_levels.append(positive)
            if negative.support >= min_support:
                next_levels.append(negative)

        levels.append(next_levels)
    return levels
        
if __name__ == '__main__':
    file = "/home/marco/Scrivania/uni/datamining/lab-data-mining/progetto/transactional_T10I4D100K.csv"
    transactions = []
    with open(file, 'r') as file:
        for line in file:
            trx = line.split(',')
            if len(trx) > 0:
                transactions.append(trx)
    min_support = int(.0001 * len(transactions)) 
    f1i = extract_first(min_support, transactions)
    sorted = sort_records(transactions, f1i)
    levels = compute_lasagna(min_support, f1i, sorted)
   #for i,level in enumerate(levels):
   #    for leaf in level:
   #        if leaf.type == True:
   #            print('Level {}'.format(i), leaf)
