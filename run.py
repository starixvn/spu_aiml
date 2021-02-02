import pandas as pd
import numpy as np
import multiprocessing as mp

import csv
import json
import warnings
import helper
import datetime
import time
import pickle
import itertools
import gc
import os
import torch

from tqdm import tqdm
from pandarallel import pandarallel
from sklearn.metrics import pairwise_distances
from mysql.connector import MySQLConnection

warnings.filterwarnings("ignore")

# define paths
root="/home/vnteam/Data/MatchData/"
orig_fn="bettrans20201129.csv"
mjl_fn="major_league.csv"
mlm_fn="match20201129.csv"
output1a="/home/vnteam/Data/SaveData/output1a/"
output1b="/home/vnteam/Data/SaveData/output1b/"
result_fn="baseline_results.csv"
match_breaking='match_breaking'

# define chunk_size for DB saving
chunk_size=10000

# define nb_workers_phase_1
nb_workers_phase_1=8

# define batch_size
batch_size=1000000

# define nb_workers_phase_2
nb_workers_phase_2=24


def separate(transdate):
    """
    >>> Input  :    '2020-09-26 7:31:01.872'
    
    >>> Output :    (2020,9,26,7,31,1)
    """
    date,hms = transdate.split(' ')[0].split('-'),transdate.split(' ')[1].split('.')[0].split(':')
    year,month,day = int(date[0]),int(date[1]),int(date[2])
    hour,min,sec = int(hms[0]),int(hms[1]),int(hms[2])
    return (year,month,day,hour,min,sec)

def distance_time(transdate1,transdate2):
    """
    >>> Input  : transdate 1 : datetime.datetime(2020,9,26,7,28,1)

                 transdate 2 : datetime.datetime(2020,9,26,7,31,1)

    >>> Output : 180 seconds
    """
    
    return (datetime.datetime(*transdate2)-datetime.datetime(*transdate1)).total_seconds()

    
def count_joining_combs(cus1,cus2):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a,comb_b=set(cus_dict[cus1]),set(cus_dict[cus2])
    return len(comb_a.intersection(comb_b))

def process_a_combination(filepath):

    """
    >>> Input    :  filepath
    >>> Output   :  pairwise-time-score matrix
    """

    # get match - bettype - league
    match=int(filepath.split('.')[0].split('_')[0])
    bettype=int(filepath.split('.')[0].split('_')[1])
    league=match_league_map[match]['leagueid']
    
    if league in MAJOR_LEAGUE_LIST:
      is_major = 1
    else:
      is_major = 0
    
    # read data of a (match,bettype) - combination    
    MATCH=pd.read_csv(os.path.join(root,match_breaking,filepath))
    
    # pick up customer list and sort it
    CUST_LIST = np.sort(MATCH.custid.unique())
    
    # get the maximum of number of tickets
    maxlen = MATCH.groupby('custid').count()['transdate'].max()
    
    # build up framework for target matrix
    # requirements : all row vectors must have the same length, here we pad -1 on the right side
    X=[]
    #for j in tqdm(range(len(CUST_LIST)),desc=f"M {match} B {bettype} | {len(CUST_LIST)} CUSTOMERS | TRASH ADDING. . ."): 
    for j in range(len(CUST_LIST)): 
        val = MATCH[MATCH['custid'] == CUST_LIST[j]][['transdate','custid']].values.flatten()       
        val = np.pad(val,(0,maxlen*2-len(val)),'constant',constant_values=-1)      
        X.append(val)
    X=np.asarray(X)

    # compute pairwise-time-score matrix
    start_compute=time.time()
    m=helper.compute_pairwise_cus(X)    
    print("\n","PAIRWISE MATRIX HAVING SHAPE %s OF MATCH %.0f BETTYPE %.0f :" % (m.shape,match,bettype),m,sep='\n')  
    print("\n","MATCH %.0f BETTYPE %.0f COMPUTING TIME SCORE TAKES %.0f SECONDS" % (match,bettype,time.time() - start_compute))
    del X,MATCH
    gc.collect()
    
    # build up result object which is a list of dictionaries whose values are positive time score
    start_transform=time.time()
        
    obj=[   
            #{"C1":int(CUST_LIST[i]),"C2":int(CUST_LIST[j]),"TS": m[i,j], "M":match,"B":bettype,"L":league,"TJC":count_joining_combs(int(CUST_LIST[i]),int(CUST_LIST[j])),"IML":is_major}
            
            #{"C1":int(CUST_LIST[i]),"C2":int(CUST_LIST[j]),"TS": m[i,j], "M":match,"B":bettype,"L":league,"TJC":type(count_joining_combs(CUST_LIST[i],CUST_LIST[j])),"IML":is_major} 
            
            {"C1":int(CUST_LIST[i]),"C2":int(CUST_LIST[j]),"TS": m[i,j], "M":match,"B":bettype,"L":league,"TJC":count_joining_combs(CUST_LIST[i],CUST_LIST[j]),"IML":is_major}
            
            for (i,j) in itertools.combinations([x for x in range(len(CUST_LIST))],2) if m[i,j] > 0   
        ]
    print(f"JSON OBJ 1th {obj[0]}",f"JSON OBJ 2nd {obj[1]}",f"JSON OBJ 3rd {obj[2]}",sep='\n')
      
    #start_save = time.time()
    # build chunks for DB saving
    chunks = [obj[x:x+chunk_size] for x in range(0, len(obj), chunk_size)]
    del m
    print("JSON OBJECT :",obj,sep="\n")
    print("\n","MATCH %.0f BETTYPE %.0f TRANSFROMING TAKES %.0f SECONDS" % (match,bettype,time.time() - start_transform))
    
    
    # filter json obj
    if len(obj) > 0:
      try:
        conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
        cursor = conn.cursor()
        for chunk in chunks:
          jsonList = json.dumps(chunk)
          cursor.callproc('SPU_AIML_InsertAssociationStatsStaging',[jsonList,None])
          conn.commit()
        cursor.close()
        conn.close()
      except Exception as err:
          print(err)
    print("\n","MATCH %.0f BETTYPE %.0f SAVING TAKES %.0f SECONDS" % (match,bettype,time.time() - start_save))
    del chunks,obj
    gc.collect()

def process_league(string_of_matches):
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


if __name__ == "__main__":
    
    # START PHASE 1
    # *****************************************************************************************************************************************************************************
    # print what time it is now !
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print("CURRENT TIME :",current_time,'\n')
    
    
    # read - filter - preprocess data
    data = pd.read_csv(os.path.join(root,orig_fn),encoding='ISO-8859-1')
    DATE = data[(data.bettype.isin([1,3,7,8]))&(data.liveindicator)]
    del data
    DATE = DATE[['custid','matchid','transdate','bettype']]
    date = DATE['transdate'].min()
    DATE['transdate'] = DATE['transdate'].apply(lambda z: distance_time(separate(date),separate(z)))
    
    # get list of matches
    matches=DATE.matchid.unique()
    
    # match breaking
    for n in tqdm(range(len(matches)),desc="MATCH BREAKING"):
        match=matches[n]
        m = DATE[DATE.matchid==match]
        for bt in [1,3,7,8]:
            f = m[m.bettype==bt]
            if f.custid.nunique() > 1:
                f.to_csv(os.path.join(root,match_breaking,f"{match}_{bt}.csv"),index=False)
    
    del DATE
    print('\n')
    
    # build cus_dict for count joining combinations
    cus_dict={}
    ls_mat=os.listdir(os.path.join(root,match_breaking))
    for k in tqdm(range(len(ls_mat)),desc="BUILD CUS DICT"):    
        fn=ls_mat[k]
        match,bt=int(fn.split('.')[0].split('_')[0]),int(fn.split('.')[0].split('_')[1])
        df = pd.read_csv(os.path.join(root,match_breaking,fn))
        
        ls = df.custid.unique()
        for cus in ls:
            if cus not in cus_dict:
                cus_dict[cus]=[(match,bt)]
            else:
                cus_dict[cus].append((match,bt))
    print('\n',f"LEN OF CUS DICT {len(cus_dict)}")
    # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
    
    # read match_league_map file and major_league list file
    match_league_map = pd.read_csv(os.path.join(root,mlm_fn),error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
    MAJOR_LEAGUE = pd.read_csv(os.path.join(root,mjl_fn))
    MAJOR_LEAGUE_LIST = MAJOR_LEAGUE.LeagueId.unique()
        
    start_processing=time.time()   
    
    candidates= os.listdir(os.path.join(root,match_breaking))
    pool=mp.Pool(nb_workers_phase_1)
    # pool.map(process_a_combination,candidates)
    # process_a_combination('39960404_3.csv')
    for _ in tqdm(pool.imap_unordered(process_a_combination,candidates),total=len(candidates),desc='MAIN PROCESS'):
      pass
    print('\n','********************************************************************************************************************************************')
    print("\n","PROCESSING TIME %.0f SECONDS" % (time.time() - start_processing))
    
