# import pandas as pd
# import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import time
import torch
import csv
import multiprocessing as mp
from pandarallel import pandarallel
from mysql.connector import MySQLConnection
import os
import pickle
import pandas as pd
import json


# define paths
root="/home/vnteam/Data/MatchData/"
orig_fn="bettrans20201129.csv"
result_fn="datastaging.csv"
mjl_fn="major_league.csv"
mlm_fn="match20201129.csv"
save_fn='cus_list.pkl'

# define batch_size
chunk_size=100000

def get_df(cus):
  # for k in tqdm(range(len(CUST_LIST)),desc="MAIN AGG"):
  try:
    print('GET INTO try')
    conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
    print('CONNECT CONN')
    cursor = conn.cursor()
    print('CONNECT CURSOR')
    # cursor.callproc('SPU_AIML_GetAssociationStatsStaging',[int(CUST_LIST[k]),int(CUST_LIST[k]),None])
    cursor.callproc('SPU_AIML_GetAssociationStatsStaging',[int(cus),int(cus),None])
    conn.commit()
    results = [r.fetchall() for r in cursor.stored_results()]
    # results = cursor.stored_results().fetchall()      
    cursor.close()
    conn.close()
    # print(f"results 1st {results[0]}")
    # print(f"type {type(results)}")
    # if len(SCORE)==0:
    #   break
    RESULTS=pd.DataFrame(results[0],columns=["C1","C2","TS","M","B","L","IMJ","TJC"])
    # RESULTS = pd.read_csv(os.path.join(root,result_fn),index_col=0,names=["C1","C2","TS","M","B","L","IMJ","TJC"],header=0)

    RESULTS=RESULTS[['C1','C2','TS','M','B','TJC']]

    print("BASELINE RESULTS",'********************',RESULTS.head(),f"RESULTS SHAPE {RESULTS.shape}",sep='\n')
    
  except Exception as err:
    #print(f"NOT FOUND CUSTOMER {cus} IN DB")
    # continue
    print(err)
  

if __name__ == "__main__":

  #start_time=time.time()
  # read - filter - preprocess data
  
  with open(os.path.join(root,save_fn),'rb') as f:
    CUST_LIST=pickle.load(f)
  
  #match_league_map = pd.read_csv(os.path.join(root,mlm_fn),error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
  #MAJOR_LEAGUE = pd.read_csv(os.path.join(root,mjl_fn))
  #MAJOR_LEAGUE_LIST = MAJOR_LEAGUE.LeagueId.unique()

  #pool=mp.Pool(12)
  #pool.map(process_a_combination,candidates)
  for _ in range(10):
    get_df(np.random.choice(CUST_LIST))
  #for _ in tqdm(pool.imap_unordered(get_df,CUST_LIST),total=len(CUST_LIST),desc='AGG'):
      #pass
  #print("***********************************************************************************************************************************************************************************")
  #print("AGG & INSERT TIME %.0f SECONDS" % (time.time() - start_time))