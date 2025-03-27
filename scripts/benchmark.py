from dataclasses import dataclass
from typing import Callable, Sequence
import sys
from os import path
sys.path.append( path.join(path.dirname(__file__), ".."))

import numpy as np
import datasets
import time
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, fpgrowth
from src.fpgrowth import fpgrowth_mp


def run_benchmark(func: Callable) -> float:
  start = time.time()
  func()
  end = time.time()

  return end - start

def run_mlxtend_algorithms(name: str, data: any, min_support: float, out: list[any]):
  
  s = time.time()
  te = TransactionEncoder().fit(data)
  df = pd.DataFrame(te.transform(dataset), columns=te.columns_)
  encoding_time = time.time() - s
  out+=[
    (name, min_support, 'mlxtend_apriori', encoding_time + run_benchmark(lambda : apriori(df, low_memory=True, min_support=min_support)) ),
    (name, min_support, 'mlxtend_fpgrowth', encoding_time + run_benchmark(lambda : fpgrowth(df, min_support=min_support)) ),
  ]

def run_fpgrowth_mp(name: str, data: any, min_support: float, out: list[any]):
  out+=[
    (name, min_support, 'fpgrowth_mp', run_benchmark(lambda : fpgrowth_mp(min_support, data)) ),
    (name, min_support, 'fpgrowth_sp', run_benchmark(lambda : fpgrowth_mp(min_support, data, max_workers=0)) ),
  ]  

BENCHMARK_DATASETS = [ 
  ('T10I4D100K', datasets.load_T10I4D100K,np.logspace(-3,-1, base=10, num=7)),
  #('T40I10D100K', datasets.load_T40I10D100K, np.logspace(-2,-1, base=10, num=7)),
  ('scontrini', datasets.load_scontrini, np.logspace(-3,-1, base=10, num=7)),
  ('retail', datasets.load_retail, np.logspace(-3,-1, base=10, num=7)),
  #('accidents', datasets.load_accidents),
  #('chess', datasets.load_chess),
  #('pumsb', datasets.load_pumsb),
  #('kosarak', datasets.load_kosarak)
]
results = []

for (name, loadfn, test_supports) in BENCHMARK_DATASETS:
  try:
    dataset = loadfn()
    for min_support in test_supports:
      run_fpgrowth_mp(name, dataset, min_support, results)
      run_mlxtend_algorithms(name, dataset, min_support, results)
      print(results[-4:])
  except FileNotFoundError:
    pass
  finally:
    pd.DataFrame(
      columns=('dataset','min_support', 'algorithm', 'runtime'),
      data=results
    ).to_csv('out.nogit.csv')

