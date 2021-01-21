import pandas as pd
import numpy as np
import multiprocessing as mp

import csv
import json
import warnings
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
cus_dict_fn="cus_dict.pkl"
match_breaking='match_breaking'


def processing(args):
    # def compute_time_score(triple):
    #     """
    #     >>> Input  :    array of transactions ID,
    #                     array of time points,
    #                     array of customers

    #     >>> Output :    time_score : a real number in range [0,1],
    #                     effective transactions ID : a set
    #     """ 
    #     cus_arr,trans_arr,time_arr = triple[:,0],triple[:,1],triple[:,2]
    #     diff_time = time_arr[1:]-time_arr[:-1]
    #     diff_cus = cus_arr[1:]-cus_arr[:-1]
    #     zip_trans = np.column_stack((trans_arr[1:],trans_arr[:-1]))
        
    #     eff_trans = zip_trans[(diff_cus != 0) & (diff_time <= 20)]
    #     fil_cus_tickets = diff_time[diff_cus != 0]
    #     fil_time_tickets = fil_cus_tickets[fil_cus_tickets <= 20]
    #     if len(fil_time_tickets)==0:
    #         time_score = 0
    #     else:
    #         time_score = (20-np.mean(fil_time_tickets)) / 20

    #     eff_trans = set(eff_trans.flatten())
    #     if len(eff_trans) == 0:
    #         eff_trans = ''
        
    #     return (time_score,','.join([str(x) for x in eff_trans]))

    def compute_time_score(SORT):
        
        time_arr,cus_arr = SORT.T
        
        diff_cus = cus_arr[1:]-cus_arr[:-1]
        #zip_trans = np.column_stack((trans_arr[1:],trans_arr[:-1]))
        zip_time = np.column_stack((time_arr[1:],time_arr[:-1]))

        #eff_trans = zip_trans[(diff_cus != 0) & (diff_time < 20)].flatten().astype(np.int64)
        eff_zip_time = zip_time[diff_cus != 0]
        #fil_cus_tickets = diff_time[diff_cus != 0]
        #eff_diff_time = fil_cus_tickets[fil_cus_tickets < 20]
        diff_time=eff_zip_time[:,0]-eff_zip_time[:,1]
        eff_diff_time=diff_time[diff_time<=20]
        if len(eff_diff_time)==0:
            time_score = 0
        else:
            time_score = (20-np.mean(eff_diff_time)) / 20

        #return (time_score, set(list(eff_trans)))
        return time_score
    
    def compute_league_score(list_minor=None,list_major=None):
        """"
        >>> Input  : list of minor leagues,list of major leagues

        >>> Output : league_score
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

    (k,j)=args
    
    a,b=ls[j],ls[k]
    info_a,info_b=big_data[a],big_data[b]

    comb_a,comb_b=set(info_a.keys()),set(info_b.keys())

    intersec = comb_a.intersection(comb_b)
    if len(intersec)>0:
        # i += 1
        #bet_count=0
        mil,mal,my_dict={},{},{}
        d = {}
        my_dict['C1']=int(a)
        my_dict['C2']=int(b)
        for comb in intersec:
        
            (match,bettype)=comb
            # arr = np.concatenate((info_a[comb],info_b[comb]),axis=0)
            arr = np.concatenate((info_a[comb][:,[0,2]],info_b[comb][:,[0,2]]),axis=0)
            # bet_count += arr.shape[0]
            l=match_league_map[match]['leagueid']
            if l in major:
                if l in mal:
                    mal[l] += 1
                
                else:
                    mal[l]=1
            else:
                if l in mil:
                    mil[l] += 1
                
                else:
                    mil[l]=1
    
            # d[str(comb)]=arr[arr[:,2].argsort()]
            d[str(comb)]=arr[arr[:,1].argsort()]

        ts_arr = pd.Series(d).apply(compute_time_score).values
        
        # ts_arr=ts_result.apply(lambda z : z[0]).values
        
        

        if len(ts_arr[ts_arr>0]) > 0:

            #my_dict['eff_trans']=ts_result.apply(lambda z : z[1]).to_dict()
            my_dict['TJSC']=len(ts_arr[ts_arr>0])
            my_dict['TJC']=len(intersec)
            my_dict['MS']=len(ts_arr[ts_arr>0]) / len(ts_arr)
            # print(f"MIL {mil.values()}",f"MAL {mal.values()}")
            my_dict['LS']=compute_league_score(list(mil.values()),list(mal.values()))
            
            # S['time_score']=S['time_score'].apply(lambda z: np.mean(np.array(z)[np.array(z) >0] if np.sum(z)>0 else 0))
            my_dict['TS']= np.mean(ts_arr[ts_arr>0])
            my_dict['BC']=1
            my_dict['TJD']=1
            return my_dict
        else:
            return ''

    else:
        return ''
        
if __name__ == "__main__":

    match_league_map = pd.read_csv(os.path.join(root,mlm_fn),error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
    MAJOR_LEAGUE = pd.read_csv(os.path.join(root,mjl_fn))
    major = MAJOR_LEAGUE.LeagueId.unique()
    # # save_dict="dict_output"

    with open(os.path.join(root,cus_dict_fn), 'rb') as f:
        big_data=pickle.load(f)
    print(f"NUM CUS {len(big_data)}","*****************************",sep='\n')

    ls=list(big_data.keys())
    pandarallel.initialize()
    i=0
    # import swifter
    myls=[]
    start=time.time()
    for k in tqdm(range(len(ls)-1),desc="Overall Progress"):
    # for k in range(6):
        for j in range(k+1,len(ls)):
            i += 1
            myls.append((k,j))
            if i==5e6:
            # print("INSERT TIME %.0f seconds" % (time.time()-start))
                # start=time.time()
                mysr=pd.Series(myls).parallel_apply(processing)
                filtered=mysr[mysr != '']
                list_of_dict=filtered.to_list()
                del myls,mysr,filtered
                chunks=[list_of_dict[x:x+100000] for x in range(0, len(list_of_dict), 100000)]
                try:
                    conn = MySQLConnection(user = 'aimlServiceAdmin', password = 'aimlServiceAdmin@AIML2209#', host = '10.40.40.78', port = '3306', database = 'SPU_AIML')
                    cursor = conn.cursor()
                    for chunk in chunks:
                        json_obj = json.dumps(chunk)
                        cursor.callproc('SPU_AIML_InsertAssociationStats',[json_obj,None])
                        conn.commit()
                    cursor.close()
                    conn.close()
                except Exception as err:
                    print(err)
                myls=[]
                i=0
                # print('\n',"SAVE TO DB %.0f seconds" % (time.time()-start_saving_to_db))