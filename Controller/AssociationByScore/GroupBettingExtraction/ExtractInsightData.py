##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
import gc
import itertools
import os
import sys
import time
sys.path.append("/\\")

import numpy as np
import pandas as pd

from Configuration.Configuration import config
from DataAccess.GroupBettingDA.AssociationStatsStaging import AssociationStatsStagingDA
from Helper import Utilities


def process_a_combination(args):
    """
    >>> Input    :  filepath
    >>> Output   :  pairwise-time-score matrix
    """
    # filepath=args[0],args[1]
    # get match - bettype - league
    filepath = args[0]
    batch_cus_dict = args[1]
    match = int(filepath.split('.')[0].split('_')[0])
    bettype = int(filepath.split('.')[0].split('_')[1])

    # read data of a (match,bettype) - combination
    MATCH = pd.read_csv(os.path.join(config.root, config.match_breaking, filepath))

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
    start_compute = time.time()
    m = Utilities.compute_pairwise_cus(X, config.time_threshold)
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
            , "TJC":Utilities.count_joining_combs_by_file_cus_dict(COMBINATION_CUST_LIST[i], COMBINATION_CUST_LIST[j], batch_cus_dict)
            , "IML":IMJ
            ,  "IN":1}

        for (i, j) in itertools.combinations([x for x in range(len(COMBINATION_CUST_LIST))], 2) if m[i, j] > 0
    ]
    # print(f"JSON OBJ 1th {obj[0]}",f"JSON OBJ 2nd {obj[1]}",f"JSON OBJ 3rd {obj[2]}",sep='\n')

    start_save = time.time()
    # build chunks for DB saving
    chunks = [obj[x:x+config.chunk_size] for x in range(0, len(obj), config.chunk_size)]
    del m
    #print("JSON OBJECT :",obj,sep="\n")
    # print("\n", "MATCH %.0f BETTYPE %.0f | %.0f CUSTOMERS | TRANSFROMING TAKES %.0f SECONDS" % (
    #     match, bettype, len(COMBINATION_CUST_LIST), time.time() - start_transform))

    # filter json obj
    if len(obj) > 0:
        association_stats_staging_da = AssociationStatsStagingDA()
        association_stats_staging_da.insert(chunks)

    # print("\n", "MATCH %.0f BETTYPE %.0f | %.0f CUSTOMERS | SAVING TAKES %.0f SECONDS" % (
    #     match, bettype, len(COMBINATION_CUST_LIST), time.time() - start_save))
    del chunks, obj
    gc.collect()
