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
from typing import List


# define paths
root="/home/vnteam/Data/MatchData/"
orig_fn="bettrans_01_31_2021.csv"
mjl_fn="major_league.csv"
mlm_fn="match20201129.csv"
output1a="/home/vnteam/Data/SaveData/output1a/"
output1b="/home/vnteam/Data/SaveData/output1b/"
result_fn="baseline_results.csv"
match_breaking='match_breaking'
cus_list_fn='cus_list.pkl'
cus_dict_fn='cus_dict.pkl'
mlm_dict_fn='match_league_map.pkl'

chunk_size=100000

batch_size=1000000

# pandarallel.initialize()

def count_joining_combs(cus1,cus2):
  """
  >>> Input   : cus1,cus2
  >>> Output  : number of joining combinations
  """
  comb_a,comb_b=set(cus_dict[cus1]),set(cus_dict[cus2])
  return len(comb_a.intersection(comb_b))

def process_league(list_of_matches):
  """
  >>> Input  : list of matches
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
      
  # list_of_matches=string_of_matches.split[',']
  matches=set(list_of_matches)
  #major,minor = [],[]
  major_dict,minor_dict = {},{}
  for match in matches:
    # list_league.add(str(league))
    # league=match_league_map[int(match)]['leagueid']
    major_or_minor=match_league_map[int(match)]
    if 'major' in major_or_minor:
      if match not in major_dict:
        major_dict[match] = 1
      else:
        major_dict[match] += 1
    else:
      if match not in minor_dict:
        minor_dict[match] = 1
      else:
        minor_dict[match] += 1
  league_score = compute_league_score(list_minor=list(minor_dict.values()),list_major=list(major_dict.values()))
  return league_score

def get_chunk(BATCH_SIZE : int,NUM_BATCH : int) -> List:
  # for k in tqdm(range(len(CUST_LIST)),desc="MAIN AGG"):
  # try:
  batch_count = 0
  chunk = []
  for ii in tqdm(range(len(LS))):
    cus = int(LS[ii])
    conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
    cursor = conn.cursor()
    # cursor.callproc('SPU_AIML_GetAssociationStatsStaging',[int(CUST_LIST[k]),int(CUST_LIST[k]),None])
    cursor.callproc('SPU_AIML_GetAssociationStatsStaging',[cus,cus,None])
    conn.commit()
    results = [r.fetchall() for r in cursor.stored_results()][0]
    # results = cursor.stored_results().fetchall()      
    cursor.close()
    conn.close()
    if len(results) > 0 :
      # batch_count += 1
      RESULTS=pd.DataFrame(results,columns=["C1","C2","TS","M","B"])
      # RESULTS = pd.read_csv(os.path.join(root,result_fn),index_col=0,names=["C1","C2","TS","M","B","L","IMJ","TJC"],header=0)

      # RESULTS=RESULTS[['C1','C2','TS','M','B','TJC']]

      # print("BASELINE RESULTS",'********************',RESULTS.head(),f"RESULTS SHAPE {RESULTS.shape}",sep='\n')
      # print("START AGGREGATE !")
      # groupby vs cus1-cus2
      # begin=time.time()
      # print("\n","START GROUPBY . . .")
      RESULTS = RESULTS.groupby(['C1','C2']).agg(lambda x: list(x)).reset_index()
      chunk += RESULTS.to_dict(orient='records')
      if len(chunk) % BATCH_SIZE == 0:
        batch_count += 1
        chunk.append(batch_count)
        chunk.append(NUM_BATCH)
        yield chunk
        chunk = []
  if chunk:
    batch_count += 1
    chunk.append(batch_count)
    chunk.append(NUM_BATCH)
    yield chunk

def aggregate(BATCH : List):

  total=BATCH.pop(-1)
  representation = BATCH.pop(-1)
  start_flow=time.time()

  begin=time.time()
  SCORE=pd.DataFrame(BATCH)
  SCORE['LS'] = SCORE['M'].apply(process_league)
  print("\n","FLOW %s / %s COMPUTED MS IN %.0f seconds !" % (representation,total,time.time()-begin))
  #print("SCORE HEAD",SCORE.head(),sep='\n')
  # compute num_effective_comb and time_score
  begin=time.time()
  # print("\n","START COMPUTING TIME SCORE | NUM EFFECTIVE COMBINATION . . .")   
  SCORE['TJSC'] = SCORE['TS'].apply(lambda z : len(z))
  SCORE['TS'] = SCORE['TS'].apply(lambda z : np.mean(z)).astype('float')
  print("\n","FLOW %s / %s COMPUTED TS & TJSC IN %.0f seconds !" % (representation,total,time.time()-begin))
  #print("SCORE HEAD",SCORE.head(),sep='\n')

  # compute number of joining matches | match score
  begin=time.time()
  # print("\n","START COMPUTING MATCH SCORE  . . .")
  SCORE['TJC'] = SCORE.apply(lambda z : count_joining_combs(z['C1'],z['C2']),axis=1)
  # SCORE['TJC'] = SCORE['TJC'].apply(lambda z : max(z))
  SCORE['MS'] = SCORE.apply(lambda z : z['TJSC']/(z['TJC']),axis=1)
  print("\n","FLOW %s / %s COMPUTED TJC & MS IN %.0f seconds !" % (representation,total,time.time()-begin))
  #print("SCORE HEAD",SCORE.head(),sep='\n')

  # merge effective matches and bettype
  begin=time.time()
  # print("\n","START MERGING MATCH LIST | BETTYPE LIST . . .")
  SCORE['ML']=SCORE['M'].apply(lambda z : ','.join([str(x) for x in z]))
  SCORE['BL']=SCORE['B'].apply(lambda z : ','.join([str(x) for x in z]))
  print("\n","FLOW %s / %s MERGED BETTYPE & MATCH IN %.0f seconds !" % (representation,total,time.time()-begin))

  SCORE['TJD']=1
  SCORE['BC']=1
  #print("SCORE HEAD",SCORE.head(),sep='\n')
  begin=time.time()
  stat=SCORE[['C1','C2','TS','MS','LS','TJC','TJSC','TJD','BC']].to_dict(orient='records')
  info=SCORE[['C1','C2','ML','BL']].to_dict(orient='records')

  chunks1 = [stat[x:x+chunk_size] for x in range(0, len(stat), chunk_size)]

  chunks2 = [info[x:x+chunk_size] for x in range(0, len(info), chunk_size)]

  try:
    conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
    cursor = conn.cursor()
    for (chunk1,chunk2) in zip(chunks1,chunks2):
      # print(f"json_obj1 {chunk1}")
      json_obj1 = json.dumps(chunk1)
      # print(f"json_obj1 {json_obj1}")
      # print(f"TYPE JSON OBJ1 {type(json_obj1)}")
      
      cursor.callproc('SPU_AIML_InsertAssociationStats',[json_obj1,None])
      conn.commit()
      json_obj2 = json.dumps(chunk2)       
      cursor.callproc('SPU_AIML_InsertAssociationSuspiciousInfo',[json_obj2,None])
      conn.commit()
  except Exception as err:
      print(err) 
  print("\n","FLOW %s / %s SAVED TO DB IN %.0f seconds !" % (representation,total,time.time()-begin))

  print("\n","TOTAL FLOW %s / %s TOOK %.0f seconds !" % (representation,total,time.time()-start_flow))


if __name__ == "__main__":

  start_time=time.time()
  
  # pandarallel.initialize()

  with open(os.path.join(root,cus_list_fn),'rb') as f:
    LS=pickle.load(f)

  with open(os.path.join(root,cus_dict_fn),'rb') as f:
    cus_dict=pickle.load(f)

  with open(os.path.join(root,mlm_dict_fn),'rb') as f:
    match_league_map=pickle.load(f)
  
  num_batch=int(np.ceil(len(LS)/batch_size))
  pool=mp.Pool(mp.cpu_count())
  chunk_gen=get_chunk(batch_size,num_batch)
  pool.map(aggregate,chunk_gen)
  print("********************************************************************************************************************************************************")
  print("AGG & INSERT TIME %.0f SECONDS" % (time.time() - start_time))