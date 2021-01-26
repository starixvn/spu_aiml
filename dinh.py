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
from itertools import islice
from multiprocessing import Manager

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
chunk_size=100000

# define nb_workers_phase_1
# nb_workers_phase_1=6

# define batch_size
batch_size=100000

# define nb_workers_phase_2
nb_workers_phase_2=24

pandarallel.initialize()

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
    # print(f"list_of_matches {list_of_matches}")
    matches=set(list_of_matches)
    # print(f"matches {matches}")
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
    # print(f'LS {league_score}')
    return league_score

def process_stat_dict(stat_dict):

    # stat_dict=args[0],args[1],args[2],args[3]

    # build stat_dict
    # stat_dict['C1']=C1
    # stat_dict['C2']=C2
    # stat_dict['TJSC']=stat_dict['TJSC']+1
    stat_dict['TS']=stat_dict['TS'] / stat_dict['TJSC']
    # stat_dict['TJC']=stat_dict['TJC']+1
    stat_dict['MS']=stat_dict['TJSC'] / stat_dict['TJC']
    # stat_dict['ML'].append(match)
    stat_dict['LS']=process_league(stat_dict['ML'])
    # stat_dict['TJD']=1
    # stat_dict['BC']=1
    # print(f"C1 {type(stat_dict['C1'])} | C2 {type(stat_dict['C2'])}   | TJSC {type(stat_dict['TJSC'])} | \
    #         TS {type(stat_dict['TS'])} | TJC {type(stat_dict['TJC'])} | MS {type(stat_dict['MS'])}     | \
    #         LS {type(stat_dict['LS'])} | TJD {type(stat_dict['TJD'])} | BC {type(stat_dict['BC'])}     |")

    return stat_dict

def process_info_dict(stat_dict):

    # stat_dict=args[0],args[1],args[2],args[3]
    # buid info_dict
    info_dict={}
    info_dict['C1']=stat_dict['C1']
    info_dict['C2']=stat_dict['C2']
    info_dict['ML']=','.join([str(x) for x in stat_dict['ML']])
    info_dict['BL']=','.join([str(x) for x in stat_dict['BL']])

    return info_dict




if __name__ == "__main__":
    
    # START PHASE 1
    # *****************************************************************************************************************************************************************************
    # print what time it is now !
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    print("CURRENT TIME :",current_time,'\n')
    
    
    # read - filter - preprocess data
    # data = pd.read_csv(os.path.join(root,orig_fn),encoding='ISO-8859-1')
    # DATE = data[(data.bettype.isin([1,3,7,8]))&(data.liveindicator)]
    # del data
    # DATE = DATE[['custid','matchid','transdate','bettype']]
    # date = DATE['transdate'].min()
    # DATE['transdate'] = DATE['transdate'].apply(lambda z: distance_time(separate(date),separate(z)))
    
    # get list of matches
    # matches=DATE.matchid.unique()
    
    # match breaking
    # for n in tqdm(range(len(matches)),desc="MATCH BREAKING"):
    #     match=matches[n]
    #     m = DATE[DATE.matchid==match]
    #     for bt in [1,3,7,8]:
    #         f = m[m.bettype==bt]
    #         if f.custid.nunique() > 1:
    #             f.to_csv(os.path.join(root,match_breaking,f"{match}_{bt}.csv"),index=False)
    
    # del DATE
    # print('\n')
    

    # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
    
    # read match_league_map file and major_league list file
    match_league_map = pd.read_csv(os.path.join(root,mlm_fn),error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
    MAJOR_LEAGUE = pd.read_csv(os.path.join(root,mjl_fn))
    MAJOR_LEAGUE_LIST = MAJOR_LEAGUE.LeagueId.unique()

    #build cus_dict for count joining combinations
    fixed_cus_dict={}
    ls_mat=os.listdir(os.path.join(root,match_breaking))
    for k in tqdm(range(len(ls_mat)),desc="BUILD CUS DICT"):    
        fn=ls_mat[k]
        match,bt=int(fn.split('.')[0].split('_')[0]),int(fn.split('.')[0].split('_')[1])
        df = pd.read_csv(os.path.join(root,match_breaking,fn))
        
        ls = df.custid.unique()
        for cus in ls:
            if cus not in fixed_cus_dict:
                fixed_cus_dict[cus]=[(match,bt)]
            else:
                fixed_cus_dict[cus].append((match,bt))
    print('\n',f"LEN OF CUS DICT {len(fixed_cus_dict)}")
    popable_cus_dict=fixed_cus_dict.copy()
    start_processing=time.time()
    # with Manager() as manager:
    # mgr = Manager()
    # ns = mgr.Namespace()
    # ns.RESULTS={}
    # ns.HISTORY={}  
    candidates= os.listdir(os.path.join(root,match_breaking))
    RESULTS,TEMP,count={},[],0
    # for i in range(2,10):
    #     RESULTS[i]={}
    for i in tqdm(range(len(candidates)),desc='MAIN PROCESS'):   
        # RESULTS=manager.dict()
        # CUS_DICT=manager.dict(cus_dict)
        # print(f"CUS_DICT {CUS_DICT}")
        
        filepath=candidates[i]
        

        # get match - bettype - league
        match=int(filepath.split('.')[0].split('_')[0])
        bettype=int(filepath.split('.')[0].split('_')[1])
        # HISTORY.add((match,bettype))

        #print(f"LENGTH HISTORY {len(HISTORY)}")
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
        # print("\n","PAIRWISE MATRIX HAVING SHAPE %s OF MATCH %.0f BETTYPE %.0f :" % (m.shape,match,bettype),m,sep='\n')  
        # print("\n","MATCH %.0f BETTYPE %.0f COMPUTING TIME SCORE TAKES %.0f SECONDS" % (match,bettype,time.time() - start_compute))
        del X,MATCH
        gc.collect()
        
        # build up result object which is a list of dictionaries whose values are positive time score
        start_transform=time.time()
      
        for i in range(len(CUST_LIST)-1):
            for j in range(i,len(CUST_LIST)):
                C1=int(CUST_LIST[i])
                C2=int(CUST_LIST[j])
                current_ts=m[i,j]
                if len(TEMP)==chunk_size:
                    count+=1
                    MY_SERIES=pd.Series(TEMP)
                    # pandarallel.initialize(nb_workers=4)
                    STAT_TEMP=MY_SERIES.parallel_apply(process_stat_dict).to_list()
                    INFO_TEMP=MY_SERIES.parallel_apply(process_info_dict).to_list()
                    try:
                        conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
                        cursor = conn.cursor()
                        json_obj1 = json.dumps(STAT_TEMP)
                        cursor.callproc('SPU_AIML_InsertAssociationStats',[json_obj1,None])
                        conn.commit()
                        json_obj2 = json.dumps(INFO_TEMP)       
                        cursor.callproc('SPU_AIML_InsertAssociationSuspiciousInfo',[json_obj2,None])
                        conn.commit()
                        cursor.close()
                        conn.close()
                        print(f"SAVING DB SUCCESSFULLY {count}th time !")
                    except Exception as err:
                        print(err)
                    # num_save_db+=chunk_size
                    TEMP = []
                    del MY_SERIES,STAT_TEMP,INFO_TEMP
                if current_ts>0:                

                    CRITICAL_TJC=len(set(popable_cus_dict[C1]).intersection(set(popable_cus_dict[C2])))
                    CONSTANT_TJC=len(set(fixed_cus_dict[C1]).intersection(set(fixed_cus_dict[C2])))
                    # prepare to push to DB
                    if CRITICAL_TJC==1:       

                        # append dicts to TEMP
                        # TEMP.append((RESULTS.pop((C1,C2))))
                        if CONSTANT_TJC==1:
                            TEMP.append(
                                        {  
                                            'TS':current_ts,'ML':[match],'BL':[bettype],'TJSC':1,
                                            'TJC':1,
                                            'TJD':1,'BC':1,'C1':C1,'C2':C2
                                        }
                                        )
                        else:
                            print(f"{C1} and {C2} WITH {CONSTANT_TJC} COMBS !")
                            MY_DICT=RESULTS[CONSTANT_TJC].pop((C1,C2))
                            MY_DICT['ML'].append(match)
                            MY_DICT['BL'].append(bettype)
                            TEMP.append(
                                        {  
                                            'TS':MY_DICT['TS']+current_ts,'ML':MY_DICT['ML'],'BL':MY_DICT['BL'],'TJSC':MY_DICT['TJSC']+1,
                                            'TJC':CONSTANT_TJC,
                                            'TJD':1,'BC':1,'C1':C1,'C2':C2
                                        }
                                        )
                    else:
                        # still in RAM
                        if CONSTANT_TJC not in RESULTS:
                            RESULTS[CONSTANT_TJC]={}
                        # else:
                        PARTITION_DICT=RESULTS[CONSTANT_TJC]
                        if (C1,C2) not in PARTITION_DICT:
                            PARTITION_DICT[(C1,C2)]=    {  
                                                        'TS':current_ts,'ML':[match],'BL':[bettype],'TJSC':1,
                                                        'TJC':CONSTANT_TJC,
                                                        'TJD':1,'BC':1,'C1':C1,'C2':C2
                                                        }
                        # else:
                        PARTITION_DICT[(C1,C2)]['TS']+=current_ts
                        PARTITION_DICT[(C1,C2)]['ML'].append(match)
                        # if len(RESULTS[(C1,C2)]['ML']) > 1:
                        #     print("Ahihi !")
                        PARTITION_DICT[(C1,C2)]['BL'].append(bettype)
                        # if len(RESULTS[(C1,C2)]['BL']) > 1:
                        #     print("Ahuhu !")
                        PARTITION_DICT[(C1,C2)]['TJSC']+=1
                    


                
        del m
        gc.collect()

        for cus in CUST_LIST:
            popable_cus_dict[cus].pop(popable_cus_dict[cus].index((match,bettype)))
        print('\n',f"MATCH {match} | BETTYPE {bettype} | {len(CUST_LIST)} CUSTOMERS",'\n')
        # for key,value in RESULTS.items():
        #     print(f"{len(value.keys())} COUPLES WITH {key} TJCs")
        del CUST_LIST
        gc.collect()
        
        # pool=mp.Pool(nb_workers_phase_1)
        #pool.map(process_a_combination,candidates)
        # process_a_combination(candidate)
        # for _ in tqdm(pool.imap_unordered(process_a_combination,[(RESULTS,CUS_DICT,candidate) for candidate in candidates]),total=len(candidates),desc='MAIN PROCESS'):
        #     pass
    print('\n','********************************************************************************************************************************************')
    print("\n","PROCESSING TIME %.0f SECONDS" % (time.time() - start_processing))

    if len(TEMP) > 0:
        MY_SERIES=pd.Series(TEMP)
        # pandarallel.initialize(nb_workers=4)
        STAT_TEMP=MY_SERIES.parallel_apply(process_stat_dict).to_list()
        INFO_TEMP=MY_SERIES.parallel_apply(process_info_dict).to_list()
        # num_save_db+=len(STAT_TEMP)
        try:
            conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
            cursor = conn.cursor()
            json_obj1 = json.dumps(STAT_TEMP)
            cursor.callproc('SPU_AIML_InsertAssociationStats',[json_obj1,None])
            conn.commit()
            json_obj2 = json.dumps(INFO_TEMP)       
            cursor.callproc('SPU_AIML_InsertAssociationSuspiciousInfo',[json_obj2,None])
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            print(err)
    
    # print(f"LENGTH OF RESULTS {len(RESULTS)}")
    #print(f"LENGTH OF RESULTS {len(COUPLE_LIST)}")
    # END PHASE 1 - START PHASE 2
    # **************************************************************************************************************************************************************************************************************
    
    # i=0
    # for item in chunks(RESULTS,chunk_size):
    #     #print item

    #     pandarallel.initialize()
    #     SCORE = pd.DataFrame(item.values(),index=item.keys()).reset_index()
    #     SCORE.columns=['C1', 'C2', 'TS', 'ML', 'BL', 'TJSC'] 

    #     # compute league score
    #     begin=time.time()
    #     print("\n","START COMPUTING LEAGUE SCORE . . .")
    #     SCORE['LS'] = SCORE['ML'].parallel_apply(process_league)
    #     print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
    #     # print("SCORE HEAD",SCORE.head(),sep='\n')

    #     # compute num_effective_comb and time_score
    #     begin=time.time()
    #     print("\n","START COMPUTING TIME SCORE | NUM EFFECTIVE COMBINATION . . .")   
    #     #SCORE['TJSC'] = SCORE['TS'].parallel_apply(lambda z : len(z))
    #     SCORE['TS'] = SCORE.parallel_apply(lambda z : z['TS']/z['TJSC'],axis=1)
    #     print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
    #     # print("SCORE HEAD",SCORE.head(),sep='\n')

    #     # compute number of joining matches | match score
    #     begin=time.time()
    #     print("\n","START COMPUTING MATCH SCORE | NUM JOINING COMBINATION . . .")
    #     SCORE['TJC'] = SCORE.parallel_apply(lambda z : count_joining_combs(z['C1'],z['C2']),axis=1)
    #     SCORE['MS'] = SCORE.parallel_apply(lambda z : z['TJSC']/z['TJC'],axis=1)
    #     print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
    #     # print("SCORE HEAD",SCORE.head(),sep='\n')

    #     # merge effective matches and bettype
    #     #begin=time.time()
    #     #print("\n","START MERGING MATCH LIST | BETTYPE LIST . . .")
    #     #SCORE['ML']=SCORE['M'].parallel_apply(lambda z : ','.join([str(x) for x in z]))
    #     #SCORE['TL']=SCORE['B'].parallel_apply(lambda z : ','.join([str(x) for x in z]))
    #     #print("\n","COMPLETED in %.0f seconds !" % (time.time()-begin))
        
    #     SCORE['TJD']=1
    #     SCORE['BC']=1
    #     print("SCORE HEAD",SCORE.head(),sep='\n')
    #     myls1=SCORE[['C1','C2','TS','MS','LS','TJC','TJSC','TJD','BC']].to_dict(orient='records')
    #     myls2=SCORE[['C1','C2','ML','BL']].to_dict(orient='records')
    #     #print("TOTAL COUPLES :",len(myls1))
    #     #json_obj1=json.dumps(myls1)
    #     #json_obj2=json.dumps(myls2)
    #     start_saving_to_db=time.time()
    #     #chunks1 = [myls1[x:x+chunk_size] for x in range(0, len(myls1), chunk_size)]
    #     #print(f"Chunks1 1 {chunks1[0]}")
    #     #print(f"TYPE CHUNKS1 {type(chunks1)}")
    #     #chunks2 = [myls2[x:x+chunk_size] for x in range(0, len(myls2), chunk_size)]
    #     #print(f"Chunks2 1 {chunks2[0]}")
    #     #print(f"TYPE CHUNKS2 {type(chunks2)}")

    #     print('\n',"SAVE BATCH %.0f  TO DB %.0f seconds" % (i,time.time()-start_saving_to_db))

    #     i += 1
    
    # print('PHASE 2 COMPLETED !','TOTAL %.0f SECONDS' % (time.time()-START_PHASE_2),'NUMBER COUPLES : > %.0f' % (i*1000000),sep='\n')
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
    
