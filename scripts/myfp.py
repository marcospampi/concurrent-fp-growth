import sys
from os import path
sys.path.append( path.join(path.dirname(__file__), ".."))

import pandas as pd
from src.fpgrowth import fpgrowth_mp, fpgrowth

if __name__ == '__main__':
    import scripts.datasets as datasets
    dataset = datasets.load_T40I10D100K()
    
    min_support = .01
    # print(dataset)

    print(fpgrowth_mp(min_support, dataset))