import json
from DataAccess.CoreDA.BaseDA import BaseDA
import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from Utilities.MultiException import ContinueGroupBetting
from DataAccess.Model.SPU_AIML.SPU_InsertAssociationStatsStagingDAModel import SPU_InsertAssociationStatsStagingDAModel
from Configuration.Configuration import config
from DataAccess.DataAccessConnection import DataAccessConnection
from DataAccess.DataAccessConnection import connection_pool_cts_datacenter,connection_pool_spu_aiml,spu_aiml,cts_datacenter
from Utilities import Utilities
from mysql.connector import MySQLConnection
import time
import os
from tqdm import tqdm
import itertools
import multiprocessing as mp
import pathos.multiprocessing as pamp
import logging
import gc
import numpy as np
import pandas as pd


class BuildDataModel(object):
    def __init__(self,*args):
        #self.pool_connection_spu_aiml = args[0]
        self.batch_cus_dict = args[0]

    def run(self):
        try:
            start_processing = time.time()
            candidates = os.listdir(os.path.join(config.root, config.match_breaking))
            
            ## another 3rd party mp
            #pool = pamp.Pool(config.nb_workers_phase_1)
            ## normal mp
            pool = mp.Pool(config.nb_workers_phase_1)
            for _ in tqdm(pool.imap_unordered(self.process_a_combination, candidates), total=len(candidates), desc='MAIN PROCESS'):
                pass
            pool.close()
            pool.join()
            print('\n', '********************************************************************************************************************************************')
            print("\n", f"{config.ENV} | PROCESSING TIME %.0f SECONDS" %
                (time.time() - start_processing))
            logging.info(
                f"{config.ENV} | Done phase 1, takes {time.time() - start_processing} seconds")
        except Exception as e:
            message_telegram = f"function BuildDataModel | {e}"
            raise ValueError(message_telegram)

    def process_a_combination(self,filepath):
        try:
            """
            >>> Input    :  filepath
            >>> Output   :  pairwise-time-score matrix
            """
            #get match - bettype - league
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
            del X, MATCH
            gc.collect()

            # build up result object which is a list of dictionaries whose values are positive time score
            start_transform = time.time()

            obj = [

                {"C1": int(COMBINATION_CUST_LIST[i]), "C2":int(COMBINATION_CUST_LIST[j]), "TS": m[i, j], "M":match, "B":bettype
                    , "L":int(leagueid)
                    , "TJC":Utilities.count_joining_combs_by_file_cus_dict(COMBINATION_CUST_LIST[i], COMBINATION_CUST_LIST[j], self.batch_cus_dict)
                    , "IML":IMJ
                    ,  "IN":1}

                for (i, j) in itertools.combinations([x for x in range(len(COMBINATION_CUST_LIST))], 2) if m[i, j] > 0
            ]
            start_save = time.time()
            # build chunks for DB saving
            chunks = [obj[x:x+config.chunk_size] for x in range(0, len(obj), config.chunk_size)]
            del m

            # filter json obj
            if len(obj) > 0:
                connection_spu = DataAccessConnection(connection_pool_spu_aiml)
                for chunk in chunks:
                    chunk = json.dumps(chunk)
                    ip_param = SPU_InsertAssociationStatsStagingDAModel(chunk)
                    BaseDA.execute("SPU_AIML_InsertAssociationStatsStaging",spu_aiml,ip_param,connection_spu)
                del connection_spu
            del chunks, obj
            gc.collect()
        except Exception as e:
            message_telegram = f"function process_a_combination | {e}"
            raise ValueError(message_telegram)