# import pandas as pd
# import matplotlib.pyplot as plt
import numpy as np
from tqdm import tqdm
import time
import multiprocessing as mp
from collections import defaultdict
from mysql.connector import MySQLConnection
import os
import pickle
import pandas as pd
import json



# define paths
root="D:\Project\Formula_BET\MatchData"
orig_fn="bettrans20201129.csv"
result_fn="datastaging.csv"
mjl_fn="major_league.csv"
mlm_fn="match20201129.csv"
cus_list_fn='cus_list.pkl'
cus_dict_fn='cus_dict.pkl'
mlm_dict_fn='match_league_map.pkl'

# define batch_size
chunk_size=100000

# pandarallel.initialize()

def count_joining_combs(cus1,cus2):
  """
  >>> Input   : cus1,cus2
  >>> Output  : number of joining combinations
  """
  comb_a,comb_b=set(cus_dict[cus1]),set(cus_dict[cus2])
  return len(comb_a.intersection(comb_b))

def is_major(x):
    major_or_minor=match_league_map[x]
    if 'major' in major_or_minor:
        return 1
    else:
        return 0

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
        
def compute_league_score(list_minor = None, list_major = None):
    
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

def total_leaguescore(x,y):
    if y == 1:
        return (x + 5/2) * (2/7)
    elif x == 1:
        return (y + 3/2) * (2/5)
    elif y!=1 and x != 1:
        minor_score = (x + 5/2) * (2/7)
        major_score = (y + 3/2) * (2/5)
        return (3 * (minor_score + 1) + (major_score + 2)) * (1/9)

def aggregate(args):
    try:
        conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
        cur = conn.cursor()
        cur.callproc('SPU_AIML_GetAssociationStatsStaging',[int(args[0]),int(args[1]),None])
        dba_results = [r.fetchall() for r in cur.stored_results()]
        conn.commit()
        cur.close()
        conn.close()
        
        if len(dba_results[0]) == 0:
              return True
        df=pd.DataFrame(dba_results[0],columns=["CustID1","CustID2","TimeScore","MatchID","Bettype"])
        #time_readfile = time.time()
        #print(df['IsMajorLeague'].unique)
        df['IsMajorLeague']=df['MatchID'].apply(lambda z : is_major(z))
        df['TotalJoiningCombs']=df.apply(lambda z : count_joining_combs(z['CustID1'],z['CustID2']),axis=1)
        first_time = time.time()
        df['sample_id'] = df['CustID1'].map(str) + df['CustID2'].map(str)

        df = df.astype({"sample_id": 'int64'})
        df['TimeScore'] =df['TimeScore'].astype('float')
        #print(df.info())
        #start_time = time.time()
        # print('Complete read file and clean data: ', time.time() - time_readfile)
        # print('-------------------------------------------------------')
        # print('Start Algorithm')
        # print('-------------------------------------------------------')
        
        df_custid = pd.DataFrame()
        df_custid = df.groupby('sample_id')[['CustID1','CustID2','TotalJoiningCombs']].first()
        #df_custid.apply(pd.DataFrame)
        #print(df_custid.head())
        #print('----------finish custid: ', time.time() - start_time)
        
        #start_time = time.time()
        df_leaguescore = pd.DataFrame()
        #print('-----group leaguescore')
        
        ## version 1
        #df_leaguescore = (df.groupby(['sample_id','IsMajorLeague', 'MatchID']).size().groupby(level=[0,1]).agg(list).unstack('IsMajorLeague'))
        
        ## version 2
        # df_leaguescore = (df.groupby(['sample_id','IsMajorLeague'])['MatchID'].apply(lambda x: x.value_counts().agg(list)).unstack('IsMajorLeague',fill_value = []))
        # df_leaguescore = (df.groupby(['sample_id','IsMajorLeague'])['MatchID'].agg(lambda x: list(x.value_counts())).unstack('IsMajorLeague',fill_value = []))
        # if 1 not in df_leaguescore:
        #     df_leaguescore[1] = [list() for x in range(len(df_leaguescore.index))]
        # if 0 not in df_leaguescore:
        #     df_leaguescore[0] = [list() for x in range(len(df_leaguescore.index))]
        
        #print(df_leaguescore.head())
        ##version 3
        # keys = df['sample_id'].astype(str) + '_' + df['IsMajorLeague'].astype(str)
        # df_parameter = (df.groupby(keys)['MatchID'].apply(lambda x: x.value_counts().agg(list)))
        #print('------finish group league: ', time.time() - start_time)
        
        ## version 4
        df_parameter = (df.groupby(['sample_id','IsMajorLeague','MatchID']).size().unstack('IsMajorLeague',fill_value=0))
        df_parameter= df_parameter.reset_index()
    
        df_parameter2 = (df.groupby(['sample_id','IsMajorLeague']).size().unstack('IsMajorLeague', fill_value=0))
        df_parameter2= df_parameter2.reset_index()
        #print(df_parameter2.info())
        #df_parameter2 = df_parameter2.drop(columns=['IsMajor'])
        df_parameter3 = pd.merge(df_parameter, df_parameter2, on=['sample_id'])
        #value_parameter = df_parameter.loc[1,0].to_list()
        if '1_x' not in df_parameter3:
            df_parameter3['1_x'] = 0
            df_parameter3['1_y'] = 0
        if '0_x' not in df_parameter3:
            df_parameter3['0_x'] = 0
            df_parameter3['0_y'] = 0
        print(df_parameter3.head())
        df_parameter3 = df_parameter3.rename({
            '0_x': 'each_league_0',
            '0_y': 'total_league_0',
            '1_x': 'each_league_1',
            '1_y': 'total_league_1' 
        }, axis=1)
        #print(df_parameter3)
        df_parameter3['score_eachleague_0'] = [(x/y)**2 if y !=0 else 0 for x,y in zip(df_parameter3['each_league_0'], df_parameter3['total_league_0'])]
        df_parameter3['score_eachleague_1'] = [(x/y)**2 if y !=0 else 0 for x,y in zip(df_parameter3['each_league_1'], df_parameter3['total_league_1'])]
        #df_parameter3 = df_parameter2.drop(columns=['total_league_0','total_league_1'])
        #print(df_parameter3.head())
        df_leaguescore = pd.DataFrame()
        df_leaguescore['minor'] = 1 - df_parameter3.groupby('sample_id')['score_eachleague_0'].sum()
        df_leaguescore['major'] = 1 - df_parameter3.groupby('sample_id')['score_eachleague_1'].sum()
        df_leaguescore['League_Score'] = df_leaguescore.apply(lambda x: total_leaguescore(x['minor'],x['major']), axis = 1)
        
        
        #start_time = time.time()
        #print('------calculate league score')
        #df_leaguescore['League_Score'] = df_leaguescore.apply(lambda x: compute_league_score(x[0],x[1]), axis = 1)
        #df_leaguescore['League_Score'] = compute_league_score(df_leaguescore[0],df_leaguescore[1])
        #print('----------finish leaguescore: ', time.time() - start_time)
        
        #start_time = time.time()
        df_timescore = df.groupby('sample_id')[['TimeScore']].mean()
        #print('----------finish timescore: ', time.time() - start_time)
        
        #start_time = time.time()
        df_matchscore = pd.DataFrame()
        df_matchscore['different'] = df.groupby(['sample_id','MatchID'])['Bettype'].nunique().groupby('sample_id').sum()
        df_matchscore['Match_Score'] = df_matchscore['different'] / df_custid['TotalJoiningCombs']
        #print('----------finish matchscore: ', time.time() - start_time)
        
        #start_time = time.time()
        df_result = pd.merge(df_custid, df_timescore, left_index=True, right_index= True)
        df_result2 = pd.merge(df_result, df_matchscore, left_index=True, right_index= True)
        #print(df_result2.head())
        df_result3 = pd.merge(df_result2, df_leaguescore,left_index=True, right_index= True)
        #print('----------finish merge: ', time.time() - start_time)
        
        #print(df_result3.info())
        #print(df_result3.head())
        
        
        ## get suspicious info
        start_time = time.time()
        df_susinfo = df.groupby('sample_id',).agg({'MatchID':lambda z:','.join([str(x) for x in list(z)]),
                                                  'Bettype':lambda z:','.join([str(x) for x in list(z)])})
        df_resultinfo = pd.merge(df_custid, df_susinfo, left_index=True, right_index=True)
       # print('----------finish merge: ', time.time() - start_time)
        
        
        #print('----------finish TOTAL TIME: ', time.time() - first_time)
        
        
        ## move to dba
        df_result3 = df_result3.drop(columns=[0,1])
        df_result3['TJD'] = 1
        df_result3['BC'] = 1
        df_result3 = df_result3.rename({
            'CustID1': 'C1',
            'CustID2': 'C2',
            'TotalJoiningCombs': 'TJC',
            'TimeScore': 'TS',
            'different': 'TJSC',
            'League_Score': 'LS',
            'Match_Score': 'MS'
        }, axis=1)
        
        ###
        df_resultinfo = df_resultinfo.drop(columns=['TotalJoiningCombs'])
        df_resultinfo = df_resultinfo.rename({
            'CustID1': 'C1',
            'CustID2': 'C2',
            'MatchID': 'ML',
            'Bettype': 'BL' 
        }, axis=1)

        fulldata_dba = df_result3.to_dict(orient="records")
        fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
        
        chunks1 = [fulldata_dba[x:x+chunk_size] for x in range(0, len(fulldata_dba), chunk_size)]

        chunks2 = [fulldatainfo_dba[x:x+chunk_size] for x in range(0, len(fulldatainfo_dba), chunk_size)]
        
        try:
          conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
          cur = conn.cursor()
          for (chunk1,chunk2) in zip(chunks1,chunks2):
            json_obj1 = json.dumps(chunk1)
            
            cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationStats',[json_obj1,date_insert,None])
            conn.commit()
            json_obj2 = json.dumps(chunk2) 
            cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo',[json_obj2,None])
            conn.commit()

          cur.close()
          conn.close()

        except Exception as err:
            print(err)
    except Exception as err:
        print(err)
    

if __name__ == "__main__":

    start_time=time.time()
    date_insert='2021-01-29'
    # read customer list
    with open(os.path.join(root,cus_list_fn),'rb') as f:
        CUST_LIST=pickle.load(f)

    with open(os.path.join(root,cus_dict_fn),'rb') as f:
        cus_dict=pickle.load(f)

    with open(os.path.join(root,mlm_dict_fn),'rb') as f:
        match_league_map=pickle.load(f)

    # build batches
    CUST_LIST=np.sort(CUST_LIST)
    BATCHES=[CUST_LIST[x:x+10] for x in range(0, len(CUST_LIST), 10)]

    # read match-league map data and major league info data

    # connect DBs
    pool=mp.Pool(10)
    for _ in tqdm(pool.imap_unordered(aggregate,[(np.min(BATCH),np.max(BATCH)) for BATCH in BATCHES]),total=len(BATCHES),desc='AGG'):
        pass

    # close DBs
    print("***********************************************************************************************************************************************************************************")
    print("AGG & INSERT TIME %.0f SECONDS" % (time.time() - start_time))