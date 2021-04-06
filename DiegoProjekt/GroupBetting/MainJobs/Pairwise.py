import sys
sys.path.append('C:/Users/diego.nguyen/diegoProj/GroupBetting')
import pandas as pd
import numpy as np
import gc
import os
import time
import json
import itertools
from numba import prange, njit, set_num_threads, jit
from numba.typed import List
import numba
from tqdm import tqdm
from Configuration.LocalConfiguration import LocalConfiguration
from Configuration.ProConfiguration import ProConfiguration
from mysql.connector import MySQLConnection
from Supporters.Helpers import count_joining_combs

ENV='LOCAL'

if ENV=='LOCAL':

    config = LocalConfiguration()

else:
    config = ProConfiguration()

root=config.GetSaveDataDir(config)
match_breaking=config.GetMatchBreaking(config)
chunk_size = int(config.getChunkSize(config))
time_threshold = int(config.GetTimeThreshold(config))

aimluser=config.getSPU_AIMLUsername(config)
aimlpwd=config.getSPU_AIMLPassword(config)
aimlhost=config.getSPU_AIMLHost(config)
aimlport=config.getSPU_AIMLPort(config)
aimldb=config.getSPU_AIMLDatabaseName(config)

@njit(parallel=True)
def compute_pairwise_cus(X,time_threshold,n_jobs=4):
    set_num_threads(n_jobs)
    n = X.shape[0]
    mat = np.empty((n, n), np.float64)
#     mat = np.repeat('', n*n).reshape(n, -1)
#     mat = list(np.arange(n*n).reshape(n, -1))

    #if save_trans :
        #transids = [np.array([0]).astype(np.int64) for _ in range(int(n*(n+1)/2) - n)]
        #for i in prange(n-1):
            #for j in range(i+1, n):
                #mat[i, j], trans = mat[j, i], trans = calculate_difference(X[i], X[j])

                #pos = int(i*n+j - i*(i+1)/2 - (i+1))
                #transids[pos] = np.array(list(trans)).astype(np.int64)

        #np.fill_diagonal(mat, 0.0)   
        #return mat, List(transids)
    
    for i in prange(n-1):
        for j in range(i+1, n):
            mat[i, j] = mat[j, i] = calculate_difference(X[i], X[j], time_threshold)

    np.fill_diagonal(mat, 0.0)   
    return mat

@njit
def calculate_difference(ls1, ls2, time_threshold):
    # drop trash
    ls1 = ls1[ls1 != -1]
    ls2 = ls2[ls2 != -1]
    
    '''reshape to [[transdate, custID],
                   [],
                   ...]
    '''
    ls1 = ls1.reshape(-1, 2)
    ls2 = ls2.reshape(-1, 2)
    
    STACK = np.vstack((ls1, ls2))
    SORT = STACK[STACK[:,0].argsort()]
    
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
        time_score = (time_threshold-np.mean(eff_diff_time)) / time_threshold

    #return (time_score, set(list(eff_trans)))
    return time_score

def doPhase1(args):
    """
    >>> Input    :  filepath,batch_cus_dict
    >>> Output   :  pairwise-time-score matrix
    """
    filepath,batch_cus_dict=args[0],args[1]
    # get match - bettype - league
    match = int(filepath.split('.')[0].split('_')[0])
    bettype = int(filepath.split('.')[0].split('_')[1])

    # read data of a (match,bettype) - combination
    MATCH = pd.read_csv(os.path.join(root, match_breaking, filepath))

    # pick up customer list and sort it
    COMBINATION_CUST_LIST = np.sort(MATCH.custid.unique())

    # get the maximum of number of tickets
    maxlen = MATCH.groupby('custid').count()['transdate'].max()

    # get leagueid
    leagueid=MATCH.leagueid.min()

    # get IMJ
    category=MATCH.category.min()
    # print(f'category {category}')
    if 'major' in category:
        IMJ=1
    else:
        IMJ=0

    # build up framework for target matrix
    # requirements : all row vectors must have the same length, here we pad -1 on the right side
    X = []
    # for j in tqdm(range(len(daily_cus_list)),desc=f"M {match} B {bettype} | {len(daily_cus_list)} CUSTOMERS | TRASH ADDING. . ."):
    for j in range(len(COMBINATION_CUST_LIST)):
        val = MATCH[MATCH['custid'] == COMBINATION_CUST_LIST[j]][[
            'transdate', 'custid']].values.flatten()
        val = np.pad(val, (0, maxlen*2-len(val)),
                     'constant', constant_values=-1)
        X.append(val)
    X = np.asarray(X)

    # compute pairwise-time-score matrix
    # start_compute = time.time()
    m = compute_pairwise_cus(X, time_threshold)
    #print("\n","PAIRWISE MATRIX HAVING SHAPE %s OF MATCH %.0f BETTYPE %.0f :" % (m.shape,match,bettype),m,sep='\n')
    # print("\n", "MATCH %.0f BETTYPE %.0f | %.0f CUSTOMERS | COMPUTING TIME SCORE TAKES %.0f SECONDS" % (
    #     match, bettype, len(COMBINATION_CUST_LIST), time.time() - start_compute))
    del X, MATCH
    gc.collect()

    # build up result object which is a list of dictionaries whose values are positive time score
    start_transform = time.time()

    obj = [

        {"C1": int(COMBINATION_CUST_LIST[i]), "C2":int(COMBINATION_CUST_LIST[j]), "TS": m[i, j], "M":match, "B":bettype
            , "L":int(leagueid)
            , "TJC":count_joining_combs(COMBINATION_CUST_LIST[i], COMBINATION_CUST_LIST[j],batch_cus_dict)
            , "IML":IMJ
            ,  "IN":1}

        for (i, j) in itertools.combinations([x for x in range(len(COMBINATION_CUST_LIST))], 2) if m[i, j] > 0
    ]
    # print(f"JSON OBJ 1th {obj[0]}",f"JSON OBJ 2nd {obj[1]}",f"JSON OBJ 3rd {obj[2]}",sep='\n')

    # start_save = time.time()
    # build chunks for DB saving
    chunks = [obj[x:x+chunk_size] for x in range(0, len(obj), chunk_size)]
    del m
    #print("JSON OBJECT :",obj,sep="\n")
    # print("\n", "MATCH %.0f BETTYPE %.0f | %.0f CUSTOMERS | TRANSFROMING TAKES %.0f SECONDS" % (
    #     match, bettype, len(COMBINATION_CUST_LIST), time.time() - start_transform))

    # filter json obj
    if len(obj) > 0:
        try:
            conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                   host=aimlhost, port=aimlport, database=aimldb)
            cursor = conn.cursor()
            for chunk in chunks:
                jsonList = json.dumps(chunk)
                in1,out1 = cursor.callproc('SPU_AIML_InsertAssociationStatsStaging', [jsonList, None])
                if out1 is not None:
                    print(out1)
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            # logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            print(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    # print("\n", "MATCH %.0f BETTYPE %.0f | %.0f CUSTOMERS | SAVING TAKES %.0f SECONDS" % (
    #     match, bettype, len(COMBINATION_CUST_LIST), time.time() - start_save))
    del chunks, obj
    gc.collect()
    # return temp_cus_list