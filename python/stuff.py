from io import TextIOWrapper
from os import path



DATASETS_PATH = path.join(path.dirname(__file__),'../datasets/')

def load_lines(file: TextIOWrapper, split_by: str ):
    result = []
    for line in file:
        try:   
            trx = [ int(x) for x in line.split(split_by) ]
            if len(trx) > 0:
                result.append(trx)
        except ValueError:
            pass    
    return result

def load_T10I4D100K():
    file = DATASETS_PATH + "transactional_T10I4D100K.csv"
    transactions = []
    with open(file, 'r') as file:
        transactions = load_lines(file, ',')
    return transactions
DATASETS_PATH = path.join(path.dirname(__file__),'../datasets/')

def load_scontrini():
    file = DATASETS_PATH + "scontrini.nogit.csv"
    transactions = []
    with open(file, 'r') as file:
        transactions = load_lines(file, ',')

    return transactions
def load_T40I10D100K():
    file = DATASETS_PATH + "T40I10D100K.dat"
    transactions = []
    with open(file, 'r') as file:
        transactions = load_lines(file, ' ')
    return transactions

def load_retail():
    file = DATASETS_PATH + "retail.dat"
    transactions = []
    with open(file, 'r') as file:
        transactions = load_lines(file, ' ')

    return transactions

def load_accidents():
    file = DATASETS_PATH + "accidents.dat"
    transactions = []
    with open(file, 'r') as file:
        transactions = load_lines(file, ' ')

    return transactions
def load_chess():
    file = DATASETS_PATH + "chess.dat"
    transactions = []
    with open(file, 'r') as file:
        transactions = load_lines(file, ' ')

    return transactions
def load_pumsb():
    file = DATASETS_PATH + "pumsb.dat"
    transactions = []
    with open(file, 'r') as file:
        transactions = load_lines(file, ' ')

    return transactions
def load_dummy():
    return [['Milk', 'Onion', 'Nutmeg', 'Kidney Beans', 'Eggs', 'Yogurt'],
           ['Dill', 'Onion', 'Nutmeg', 'Kidney Beans', 'Eggs', 'Yogurt'],
           ['Milk', 'Apple', 'Kidney Beans', 'Eggs'],
           ['Milk', 'Unicorn', 'Corn', 'Kidney Beans', 'Yogurt'],
           ['Corn', 'Onion', 'Onion', 'Kidney Beans', 'Ice cream', 'Eggs']]