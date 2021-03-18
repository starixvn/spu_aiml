# import pandas as pd
# import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import time
import matplotlib.pyplot as plt
import csv
import multiprocessing as mp
# from pandarallel import pandarallel
# from mysql.connector import MySQLConnection
import os
import pickle
import pandas as pd
import json


if __name__ == "__main__":

  # define paths
  path="C:/Users/diego.nguyen/Downloads/Big Small/Big Small/20210305-txturbo_phiens_bk.csv"
  data=pd.read_csv(path)
  X=data[['dice1','dice2','dice3']].values
  sortedX=np.sort(X,axis=0)
  nloops=sortedX.shape[0]
  window_size=72
  ls=[]
  for nloop in tqdm(range(nloops-window_size)):
    partition=sortedX[nloop:nloop+window_size]
    DISTINCT_ARR=np.unique(partition,axis=0)
    nb_unique=DISTINCT_ARR.shape[0]
    ls.append(nb_unique)
    if nb_unique==56:
      print(f'Special Index {nloop} appeared !')
  print(f'MAX ls {max(ls)}',f'MIN ls {min(ls)}',sep='\n')
  plt.hist(ls)
  plt.show()