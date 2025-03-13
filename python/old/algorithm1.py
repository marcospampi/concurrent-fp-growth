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

def compute_upwards_tree(min_support: int, fi: dict[FrequentItem], transactions: list[list[int]]):
    in_transaction_ptr = [0] * len(transactions)
    levels = [[Level(parent = -1,begin=0, end=len(transactions), support=len(transactions), type=True)]]
    to_transaction = list(range(len(transactions)))
    copy = to_transaction[:]


    for current_item in range(len(fi)):
        next_levels = []
        for parent, level in enumerate(levels[-1]):
            head, tail = level.begin, level.end
            ok = 0
            for i in range(level.begin, level.end):
                tid = copy[i]
                ptr = in_transaction_ptr[tid]
                if ptr != -1:
                    trx = transactions[tid]
                    accept = trx[ptr] == current_item
                    if accept:
                        copy[head] = tid
                        head = head + 1
                        ptr+=1
                        in_transaction_ptr[tid] = ptr if ptr < len(transactions[tid]) else -1
                        ok+=1
                    else:
                        tail = tail -1
                        copy[tail] = tid
                else:
                    # rimane della munnizza! => bin
                    print(trx, ptr, level, current_item)
            
            positive = Level(parent, level.begin, head, ok, type=True)
            negative = Level(parent, head, level.end, level.end - head, type=False)
            if positive.support >= min_support:
                next_levels.append(positive)
            if negative.support >= min_support:
                next_levels.append(negative)

        to_transaction, copy = copy, to_transaction     
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
    levels = compute_upwards_tree(min_support, f1i, sorted)
    # for i,level in enumerate(levels):
    #     print("Level {}".format(i))
    #     for leaf in level:
    #         if leaf.type == True:
    #             print('\t', leaf)
