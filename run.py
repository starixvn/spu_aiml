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
    #chunks = [obj[x:x+chunk_size] for x in range(0, len(obj), chunk_size)]
    #del m,obj
    #print("JSON OBJECT :",obj,sep="\n")
    #print("\n","MATCH %.0f BETTYPE %.0f TRANSFROMING TAKES %.0f SECONDS" % (match,bettype,time.time() - start_transform))
    
    
    # filter json obj
    #if len(obj) > 0:
      #try:
        #conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
        #cursor = conn.cursor()
        #for chunk in chunks:
          #jsonList = json.dumps(chunk)
          #cursor.callproc('SPU_AIML_InsertAssociationStatsStaging',[jsonList,None])
          #conn.commit()
        #cursor.close()
        #conn.close()
      #except Exception as err:
          #print(err)
    #print("\n","MATCH %.0f BETTYPE %.0f SAVING TAKES %.0f SECONDS" % (match,bettype,time.time() - start_save))
    #del chunks
    #gc.collect()

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
    #t = time.localtime()
    #current_time = time.strftime("%H:%M:%S", t)
    #print("CURRENT TIME :",current_time,'\n')
    
    
    # read - filter - preprocess data
    #data = pd.read_csv(os.path.join(root,orig_fn),encoding='ISO-8859-1')
    #DATE = data[(data.bettype.isin([1,3,7,8]))&(data.liveindicator)]
    #del data
    #DATE = DATE[['custid','matchid','transdate','bettype']]
    #date = DATE['transdate'].min()
    #DATE['transdate'] = DATE['transdate'].apply(lambda z: distance_time(separate(date),separate(z)))
    
    # get list of matches
    #matches=DATE.matchid.unique()
    
    # match breaking
    #for n in tqdm(range(len(matches)),desc="MATCH BREAKING"):
        #match=matches[n]
        #m = DATE[DATE.matchid==match]
        #for bt in [1,3,7,8]:
            #f = m[m.bettype==bt]
            #if f.custid.nunique() > 1:
                #f.to_csv(os.path.join(root,match_breaking,f"{match}_{bt}.csv"),index=False)
    
    #del DATE
    #print('\n')
    
    # build cus_dict for count joining combinations
    #cus_dict={}
    #ls_mat=os.listdir(os.path.join(root,match_breaking))
    #for k in tqdm(range(len(ls_mat)),desc="BUILD CUS DICT"):    
        #fn=ls_mat[k]
        #match,bt=int(fn.split('.')[0].split('_')[0]),int(fn.split('.')[0].split('_')[1])
        #df = pd.read_csv(os.path.join(root,match_breaking,fn))
        
        #ls = df.custid.unique()
        #for cus in ls:
            #if cus not in cus_dict:
                #cus_dict[cus]=[(match,bt)]
            #else:
                #cus_dict[cus].append((match,bt))
    #print('\n',f"LEN OF CUS DICT {len(cus_dict)}")
    #print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
    
    # read match_league_map file and major_league list file
    match_league_map = pd.read_csv(os.path.join(root,mlm_fn),error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
    MAJOR_LEAGUE = pd.read_csv(os.path.join(root,mjl_fn))
    MAJOR_LEAGUE_LIST = MAJOR_LEAGUE.LeagueId.unique()
        
    #start_processing=time.time()   
    
    #candidates= os.listdir(os.path.join(root,match_breaking))
    #pool=mp.Pool(nb_workers_phase_1)
    #pool.map(process_a_combination,candidates)
    #process_a_combination('39960404_3.csv')
    #for _ in tqdm(pool.imap_unordered(process_a_combination,candidates),total=len(candidates),desc='MAIN PROCESS'):
      #pass
    #print('\n','********************************************************************************************************************************************')
    #print("\n","PROCESSING TIME %.0f SECONDS" % (time.time() - start_processing))
    
    
    # END PHASE 1 - START PHASE 2
    # **************************************************************************************************************************************************************************************************************
    START_PHASE_2=time.time()
    i=0
    while True:
        try:
        conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
        cursor = conn.cursor()
        cursor.callproc('SPU_AIML_GetCouplePreStats',[i*batch_size,batch_size,None])
        conn.commit()
        results = [r.fetchall() for r in cursor.stored_results()]
        cursor.close()
        conn.close()
        except Exception as err:
        print(err)
        
        SCORE=pd.DataFrame(results,names=["C1","C2","TS","TJSM","TJM","ML","BL"])
        if len(SCORE)==0:
        break
        #with open(os.path.join(root,cus_dict_directory,cus_dict_fn),'rb') as h:
        #cus_dict=pickle.load(h)

        #RESULTS = pd.read_csv(os.path.join(output1a,result_fn),index_col=0,names=["C1","C2","TS","M","B"],header=0)

        #print("BASELINE RESULTS",'********************',RESULTS.head(),f"RESULTS SHAPE {RESULTS.shape}",sep='\n')
        #print("START AGGREGATE !")
        # groupby vs cus1-cus2
        #begin=time.time()
        #print("\n","START GROUPBY . . .")
        #SCORE = RESULTS.groupby(['C1','C2']).agg(lambda x: list(x)).reset_index()
        #print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))

        pandarallel.initialize() 
        # compute league score
        begin=time.time()
        print("\n","START COMPUTING LEAGUE SCORE . . .")
        SCORE['LS'] = SCORE['M'].parallel_apply(process_league)
        print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
        #print("SCORE HEAD",SCORE.head(),sep='\n')
  
        # compute num_effective_comb and time_score
        #begin=time.time()
        #print("\n","START COMPUTING TIME SCORE | NUM EFFECTIVE COMBINATION . . .")   
        #SCORE['TJSM'] = SCORE['TS'].parallel_apply(lambda z : len(z))
        #SCORE['TS'] = SCORE['TS'].parallel_apply(lambda z : np.mean(z))
        #print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
        #print("SCORE HEAD",SCORE.head(),sep='\n')

        # compute number of joining matches | match score
        begin=time.time()
        #print("\n","START COMPUTING MATCH SCORE | NUM JOINING COMBINATION . . .")
        #SCORE['TJM'] = SCORE.parallel_apply(lambda z : count_joining_combs(z['C1'],z['C2']),axis=1)
        #SCORE['TJM'] = SCORE.parallel_apply(lambda z : len(cus_dict[z['C1']].intersection(cus_dict[z['C2']])),axis=1)
        SCORE['MS'] = SCORE['TJSM'] / SCORE['TJM']
        print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
        #print("SCORE HEAD",SCORE.head(),sep='\n')

        # merge effective matches and bettype
        #begin=time.time()
        #print("\n","START MERGING MATCH LIST | BETTYPE LIST . . .")
        #SCORE['ML']=SCORE['M'].parallel_apply(lambda z : ','.join([str(x) for x in z]))
        #SCORE['TL']=SCORE['B'].parallel_apply(lambda z : ','.join([str(x) for x in z]))
        #print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
      
        SCORE['TJD']=1
        SCORE['BC']=1
        #print("SCORE HEAD",SCORE.head(),sep='\n')
        myls1=SCORE[['C1','C2','TS','MS','LS','TJM','TJSM','TJD','BC']].to_dict(orient='records')
        myls2=SCORE[['C1','C2','ML','BL']].to_dict(orient='records')
        #print("TOTAL COUPLES :",len(myls1))
        #json_obj1=json.dumps(myls1)
        #json_obj2=json.dumps(myls2)
        start_saving_to_db=time.time()
        #chunks1 = [myls1[x:x+chunk_size] for x in range(0, len(myls1), chunk_size)]
        #print(f"Chunks1 1 {chunks1[0]}")
        #print(f"TYPE CHUNKS1 {type(chunks1)}")
        #chunks2 = [myls2[x:x+chunk_size] for x in range(0, len(myls2), chunk_size)]
        #print(f"Chunks2 1 {chunks2[0]}")
        #print(f"TYPE CHUNKS2 {type(chunks2)}")
    
    
    
        try:
        conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
        cursor = conn.cursor()
        def save_to_db(args):
            json_obj1 = json.dumps(args[0])
            cursor.callproc('SPU_AIML_InsertAssociationStats',[json_obj1,None])
            conn.commit()
            json_obj2 = json.dumps(args[1])
            cursor.callproc('SPU_AIML_InsertAssociationSuspiciousInfo',[json_obj2,None])
            conn.commit()
        pool=mp.Pool(nb_workers_phase_2)
        #for (chunk1,chunk2) in zip(chunks1,chunks2):
            #json_obj1 = json.dumps(chunk1)
            #print(f"json_obj1 {json_obj1}")
            #print(f"TYPE JSON OBJ1 {type(json_obj1)}")
            
            #cursor.callproc('SPU_AIML_InsertAssociationStats',[json_obj1,None])
            #conn.commit()
            #json_obj2 = json.dumps(chunk2)       
            #cursor.callproc('SPU_AIML_InsertAssociationSuspiciousInfo',[json_obj2,None])
            #conn.commit()
        pool.map(save_to_db,[x for x in zip (
                                            [myls1[x:x+chunk_size] for x in range(0, len(myls1), chunk_size)],
                                            [myls2[x:x+chunk_size] for x in range(0, len(myls2), chunk_size)]
                                            )
                            ]
                )
        cursor.close()
        conn.close()
        except Exception as err:
        print(err)
        print('\n',"SAVE TO DB %.0f seconds" % (time.time()-start_saving_to_db))
        
        i += 1
    
    print('PHASE 2 COMPLETED !','TOTAL %.0f SECONDS' % (time.time()-START_PHASE_2),'NUMBER COUPLES : > %.0f' % (i*1000000),sep='\n')
    # PHASE 2 WITH PROCESSING IN DB
    # ********************************************************************************************************************************************************************************    
    #try:
        #conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
        #cursor = conn.cursor()
        #cursor.callproc('SPU_AIML_ComputeDailyScore',[None])
        #conn.commit()
        #cursor.close()
        #conn.close()
    #except Exception as err:
        #print(err)
    
