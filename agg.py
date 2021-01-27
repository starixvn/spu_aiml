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

# pandarallel.initialize()

def process_league(string_of_matches):
  """
  >>> Input  : string of matches
  >>> Output : league_score
  """

  def compute_league_score(list_minor = None, list_major = None):
    """"
    >>> Input  :    list_minor, list of number of match in minor league
                    list_major, list of number of match in major league

    >>> Output :    league_score
    """
    def gini_score(lista):
      """
      >>> Input  : list of integer,each represents quantity of some class
      >>> Output : gini score
      ------------------------
      Example

      > Input  : [1,1]
      > Output : .5
      """
      sum_match = sum(lista)

      return 1 - sum(map(lambda x:(x/sum_match)**2,lista))

    gini_minor = gini_score(list_minor)
    gini_major = gini_score(list_major)
    if len(list_minor) == 0:
      league_score = (gini_major + 3/2) * (2/5)
    elif len(list_major) == 0:
      league_score = (gini_minor + 5/2) * (2/7)
    else:
      minor_score = (gini_minor + 5/2) * (2/7)
      major_score = (gini_major + 3/2) * (2/5)
      league_score = (3 * (minor_score + 1) + (major_score + 2)) * (1/9)
    return league_score
      
  list_of_matches=string_of_matches.split[',']
  matches=set(list_of_matches)
  #major,minor = [],[]
  major_dict,minor_dict = {},{}
  for match in matches:
    # list_league.add(str(league))
    league=match_league_map[int(match)]['leagueid']
    if league in MAJOR_LEAGUE_LIST:
      if league not in major_dict:
        major_dict[league] = 1
      else:
        major_dict[league] += 1
    else:
      if league not in minor_dict:
        minor_dict[league] = 1
      else:
        minor_dict[league] += 1
  league_score = compute_league_score(list_minor=list(minor_dict.values()),list_major=list(major_dict.values()))
  return league_score

def aggregate(args):
  # for k in tqdm(range(len(CUST_LIST)),desc="MAIN AGG"):
  try:
    # conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
    # cursor = conn.cursor()
    # cursor.callproc('SPU_AIML_GetAssociationStatsStaging',[int(CUST_LIST[k]),int(CUST_LIST[k]),None])
    cursor.callproc('SPU_AIML_GetAssociationStatsStaging',[args[0],args[1],None])
    conn.commit()
    results = [r.fetchall() for r in cursor.stored_results()]
    # results = cursor.stored_results().fetchall()      
    # cursor.close()
    # conn.close()
    # print(f"results 1st {results[0]}")
    # print(f"type {type(results)}")
    # if len(SCORE)==0:
    #   break
    RESULTS=pd.DataFrame(results[0],columns=["C1","C2","TS","ML","BL","L","IMJ","TJC"])
    # RESULTS = pd.read_csv(os.path.join(root,result_fn),index_col=0,names=["C1","C2","TS","M","B","L","IMJ","TJC"],header=0)

    RESULTS=RESULTS[['C1','C2','TS','ML','BL','TJC']]

    # print("BASELINE RESULTS",'********************',RESULTS.head(),f"RESULTS SHAPE {RESULTS.shape}",sep='\n')
    # print("START AGGREGATE !")
    # groupby vs cus1-cus2
    begin=time.time()
    # print("\n","START GROUPBY . . .")
    SCORE = RESULTS.groupby(['C1','C2']).agg({
                                              'TS':['mean','count'],'TJC':'max',
                                              'M':lambda z:','.join([str(x) for x in list(z)]),
                                              'B':lambda z:','.join([str(x) for x in list(z)])
                                              }).reset_index()
    # print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))``

    SCORE.columns=['C1','C2','TS','TJSC','ML','BL','TJC']
    # compute league score
    # begin=time.time()
    # print("\n","START COMPUTING LEAGUE SCORE . . .")
    SCORE['LS'] = SCORE['ML'].apply(process_league)
    # print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
    #print("SCORE HEAD",SCORE.head(),sep='\n')
    # compute num_effective_comb and time_score
    # begin=time.time()
    # print("\n","START COMPUTING TIME SCORE | NUM EFFECTIVE COMBINATION . . .")   
    # SCORE['TJSC'] = SCORE['TS'].apply(lambda z : len(z))
    # SCORE['TS'] = SCORE['TS'].apply(lambda z : np.mean(z)).astype('float')
    # print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
    #print("SCORE HEAD",SCORE.head(),sep='\n')

    # compute number of joining matches | match score
    # begin=time.time()
    # print("\n","START COMPUTING MATCH SCORE  . . .")
    #SCORE['TJM'] = SCORE.parallel_apply(lambda z : count_joining_combs(z['C1'],z['C2']),axis=1)
    # SCORE['TJC'] = SCORE['TJC'].apply(lambda z : max(z))
    SCORE['MS'] = SCORE['TJSC']/(SCORE['TJC']
    # print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
    #print("SCORE HEAD",SCORE.head(),sep='\n')

    # merge effective matches and bettype
    # begin=time.time()
    # print("\n","START MERGING MATCH LIST | BETTYPE LIST . . .")
    # SCORE['ML']=SCORE['M'].apply(lambda z : ','.join([str(x) for x in z]))
    # SCORE['BL']=SCORE['B'].apply(lambda z : ','.join([str(x) for x in z]))
    #print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))

    SCORE['TJD']=1
    SCORE['BC']=1
    #print("SCORE HEAD",SCORE.head(),sep='\n')
    myls1=SCORE[['C1','C2','TS','MS','LS','TJC','TJSC','TJD','BC']].to_dict(orient='records')
    myls2=SCORE[['C1','C2','ML','BL']].to_dict(orient='records')

    # print("TOTAL COUPLES :",len(myls1))
    #json_obj1=json.dumps(myls1)
    #json_obj2=json.dumps(myls2)
    start_saving_to_db=time.time()
    chunks1 = [myls1[x:x+chunk_size] for x in range(0, len(myls1), chunk_size)]
    #print(f"Chunks1 1 {chunks1[0]}")
    #print(f"TYPE CHUNKS1 {type(chunks1)}")
    chunks2 = [myls2[x:x+chunk_size] for x in range(0, len(myls2), chunk_size)]
    #print(f"Chunks2 1 {chunks2[0]}")
    #print(f"TYPE CHUNKS2 {type(chunks2)}")
  
  
  
    try:
      # conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
      # cursor = conn.cursor()
      for (chunk1,chunk2) in zip(chunks1,chunks2):
        # print(f"json_obj1 {chunk1}")
        json_obj1 = json.dumps(chunk1)
        # print(f"json_obj1 {json_obj1}")
        # print(f"TYPE JSON OBJ1 {type(json_obj1)}")
        
        # cursor.callproc('SPU_AIML_InsertAssociationStats',[json_obj1,None])
        cursor.callproc('SPU_AIML_InsertAssociationStats',[json_obj1,None])
        conn.commit()
        json_obj2 = json.dumps(chunk2)       
        cursor.callproc('SPU_AIML_InsertAssociationSuspiciousInfo',[json_obj2,None])
        conn.commit()
    except Exception as err:
      print(err)
  except Exception as err:
    # print(f"NOT FOUND CUSTOMER {cus} IN DB")
    # continue
    print("THIS BATCH DOES NOT HAVE IN DB",err,sep='\n')
  

if __name__ == "__main__":

  start_time=time.time()

  # read customer list
  with open(os.path.join(root,save_fn),'rb') as f:
    CUST_LIST=pickle.load(f)
  
  # build batches
  CUST_LIST=np.sort(CUST_LIST)
  BATCHES=[CUST_LIST[x:x+10] for x in range(0, len(CUST_LIST), 10)]

  # read match-league map data and major league info data
  match_league_map = pd.read_csv(os.path.join(root,mlm_fn),error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
  MAJOR_LEAGUE = pd.read_csv(os.path.join(root,mjl_fn))
  MAJOR_LEAGUE_LIST = MAJOR_LEAGUE.LeagueId.unique()

  # connect DBs
  conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
  cursor = conn.cursor()

  pool=mp.Pool(24)
  for _ in tqdm(pool.imap_unordered(aggregate,[(np.min(BATCH),np.max(BATCH)) for BATCH in BATCHES]),total=len(BATCHES),desc='AGG'):
      pass
  
  # close DBs
  cursor.close()
  conn.close()
  
  print("***********************************************************************************************************************************************************************************")
  print("AGG & INSERT TIME %.0f SECONDS" % (time.time() - start_time))