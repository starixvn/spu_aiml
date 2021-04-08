import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
#sys.path.append("D:\\Project\\aiml_cleancode\\")
import pandas as pd
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
import logging
import csv
import re
import json
import warnings
from GroupBetting.MainJobs import AggDayEnd
from GroupBetting.MainJobs import AggOnTheFly
from GroupBetting.MainJobs import GroupbyIP
from GroupBetting.MainJobs import Prepare_DataTS
from GroupBetting.Support import Function_Support
#from GroupBetting.Support import helper
from GroupBetting.Support import SendLogTelegram
import datetime
import time
import pickle
import itertools
import gc
import os
import torch

from tqdm import tqdm
#from pandarallel import pandarallel
# from sklearn.metrics import pairwise_distances
from mysql.connector import MySQLConnection
from Configuration.Configuration import Configuration

from datetime import date as dt
from datetime import timedelta

warnings.filterwarnings("ignore")

ENV='LOCAL'
if ENV=='LOCAL':
    config = Configuration("localconfig.ini",ENV)
else:
    config = Configuration("proconfig.ini",ENV)
    
if __name__ == "__main__":
    #region Clear and Clean Data
    conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                            host=config.aimlhost, port=config.aimlport, database=config.aimldb)
    cur = conn.cursor()
    # Truncate table AssociationStatsStaging
    cur.callproc('SPU_AIML_DBA_Truncate_Table',
                ['AssociationStatsStaging'])
    conn.commit()
    check_cus_files=os.listdir(config.root)
    if config.cus_list_fn in check_cus_files:
        os.remove(os.path.join(config.root,config.cus_list_fn))
    if config.cus_dict_fn in check_cus_files:
        os.remove(os.path.join(config.root,config.cus_dict_fn))
    initial = []
    #endregion
    while True:
        check_files = [f for f in sorted(os.listdir(config.root_orig))]
        if len(check_files) > 0:
            orig_fn = check_files[0]
            myStrCheck = check_files[0].rsplit("_",4)
            pattern = "^" + myStrCheck[0]
            check_files_sameday = [i for i in check_files if re.findall(pattern,i)]
            if initial==[]:
                month_prev=orig_fn.split('.')[0].split('_')[1]
                day_prev=orig_fn.split('.')[0].split('_')[2]
                year_prev=orig_fn.split('.')[0].split('_')[3]
                time_begin = time.time()
                today = dt.today()
                logging.info(
                    "======================================================================================================")
                logging.info(f"{ENV} | Running for Date: {year_prev+'-'+month_prev+'-'+day_prev}")
                message_telegram = f"{ENV} | Group Betting is running for {year_prev+'-'+month_prev+'-'+day_prev}"
                SendLogTelegram.send_message(message_telegram)
                initial.append(day_prev)
            

            # START PHASE 0 --> PREPARATION
            # *****************************************************************************************************************************************************************************
            try:
                time_phase0 = time.time()
                t = time.localtime()
                current_time = time.strftime("%H:%M:%S", t)
                
                print(f"{ENV} | CURRENT TIME : ", current_time)
                logging.info(f'Start running file {orig_fn}')
                logging.info(f"Total file: {len(check_files_sameday)}")
                
                ### use list comprehensive to concat data
                data = pd.concat((pd.read_csv(os.path.join(config.root_orig, f),encoding='ISO-8859-1', skiprows=[1], skipfooter=1).assign(file_name = f) for f in check_files_sameday))
                
                #for file in check_files_sameday:
                    #os.rename(os.path.join(config.root_orig,file),os.path.join(config.backup,file))
                logging.info(f"Number of rows: {len(data)}")
                
                if len(data.index)==0:
                    for file in check_files_sameday:
                        os.remove(os.path.join(config.root_orig, file))
                    continue
                
                if data.bettype.isnull().values.any():
                    logging.error(f'File Error {orig_fn} | Bettype Column Null')
                    print(f'File Error {orig_fn} | Bettype Column Null')
                    for file in check_files_sameday:
                        os.rename(os.path.join(config.root_orig, file),os.path.join(config.root,'NullBettype',file))
                    continue
                
                ### clean missing data
                data.dropna(subset=['custid', 'matchid', 'transdate', 'bettype','leagueid'],inplace=True)
                df_nan = data[data[['custid', 'matchid', 'transdate', 'bettype','leagueid']].isna().any(axis=1)]
                
                if len(df_nan.index) != 0:
                    data.to_csv(config.errorFolder+f"file_error_data_{time.time()}.csv",index=False)
                    #count +=1
                DATE = data[(data.bettype.isin([1, 3, 7, 8]))
                            & (data.liveindicator)]
                df_dataip = data[(data.bettype.isin([1, 3, 7, 8]))
                        & (data.liveindicator)]
                if len(DATE.index)==0:
                    logging.error(f'File Error {orig_fn} | No Live')
                    print(f'File Error {orig_fn} | No Live')
                    os.rename(os.path.join(config.root_orig, orig_fn),os.path.join(config.root,'NoLive',orig_fn))
                    continue

                date_winlost = DATE['winlostdate'].min()
                # print(f'date_winlost {date_winlost}')
                DATE['category'] = DATE['category'].fillna(value='minor')
                DATE['category'] = DATE['category'].astype('str')
                DATE['category'] = DATE['category'].str.lower()
                DATE = DATE[['custid', 'matchid', 'transdate', 'bettype','leagueid','category']]
                date = DATE['transdate'].min()
                date_insert = date_winlost.split()[0]
                # date_insert='2021-01-29'
                print(f"date insert {date_insert}")
                DATE['transdate'] = DATE['transdate'].apply(
                    lambda z: Function_Support.distance_time(Function_Support.separate(date), Function_Support.separate(z)))

                # get list of matches
                matches = DATE.matchid.unique()
                # print(f'Number of matches {len(matches)}')

                # get list of custid
                batch_cus_list = list(DATE.custid.unique())
                check_cus_files=os.listdir(os.path.join(config.root))
                # print(f'check_cus_list_file {check_cus_list_file}')
                if config.cus_list_fn not in check_cus_files:
                    with open(os.path.join(config.root, config.cus_list_fn), 'wb') as f:
                        pickle.dump(batch_cus_list, f)
                else:
                    with open(os.path.join(config.root, config.cus_list_fn), 'rb') as f:
                        daily_cus_list = pickle.load(f)
                    daily_cus_list+=batch_cus_list
                    daily_cus_list=list(set(daily_cus_list))
                    with open(os.path.join(config.root, config.cus_list_fn), 'wb') as f:
                        pickle.dump(daily_cus_list, f)

                # match breaking
                check_match_files=os.listdir(os.path.join(config.root, config.match_breaking))
                if len(check_match_files)>0:
                    for fn in check_match_files:
                        os.remove(os.path.join(config.root, config.match_breaking,fn))
                for n in tqdm(range(len(matches)), desc="MATCH BREAKING"):
                    match = matches[n]
                    m = DATE[DATE.matchid == match]
                    for bt in [1, 3, 7, 8]:
                        f = m[m.bettype == bt]
                        if f.custid.nunique() > 1:
                            f.to_csv(os.path.join(config.root, config.match_breaking,
                                                f"{match}_{bt}.csv"), index=False)

                del DATE, data
                print('\n')

                # build cus_dict for count joining combinations
                batch_cus_dict = {}
                ls_mat = os.listdir(os.path.join(config.root, config.match_breaking))
                for k in tqdm(range(len(ls_mat)), desc="BUILD CUS DICT"):
                    fn = ls_mat[k]
                    match, bt = int(fn.split('.')[0].split('_')[0]), int(
                        fn.split('.')[0].split('_')[1])
                    df = pd.read_csv(os.path.join(config.root, config.match_breaking, fn))

                    ls = df.custid.unique()
                    for cus in ls:
                        if cus not in batch_cus_dict:
                            batch_cus_dict[cus] = [(match, bt)]
                        else:
                            batch_cus_dict[cus].append((match, bt))
                if config.cus_dict_fn not in check_cus_files:
                    with open(os.path.join(config.root, config.cus_dict_fn), 'wb') as g:
                        pickle.dump(batch_cus_dict, g)
                else:
                    with open(os.path.join(config.root, config.cus_dict_fn), 'rb') as g:
                        daily_cus_dict = pickle.load(g)
                    for key,value in batch_cus_dict.items():
                        if key not in daily_cus_dict:
                            daily_cus_dict[key]=value
                        else:
                            daily_cus_dict[key]+=value
                    with open(os.path.join(config.root, config.cus_dict_fn), 'wb') as g:
                        pickle.dump(daily_cus_dict, g)
                # print('\n', f"LEN OF CUS DICT {len(cus_dict)}")
                with open(os.path.join(config.root, config.cus_dict_fn), 'rb') as g:
                        daily_cus_dict = pickle.load(g)
                logging.info(
                    f"{ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
                # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
            except Exception as e:
                message_telegram = f"{ENV} | Error at phase 0: {e}"
                Function_Support.notify_logging(message_telegram)
                break

            # START PHASE ASSOCIATION BY IP 
            # *****************************************************************************************************************************************************************************
            try:
                logging.info(f"{ENV} |Group Betting by IP is running")
                # message_telegram = f"{ENV} |Group Betting by IP is running"
                # SendLogTelegram.send_message(message_telegram)
                df_dataip = df_dataip[['custid','ip','bettype','matchid','leagueid','homeid','awayid','transdate']]
                GroupbyIP.AssociationbyIP(df_dataip,date_insert,config)
                del df_dataip
            except Exception as e:
                message_telegram = f"{ENV} | Error at phase Association by IP: {e}"
                Function_Support.notify_logging(message_telegram)
                break
            # END PHASE 0 - START PHASE 1
            # ****************************************************************************************************************************************************************************
            try:
                start_processing = time.time()

                candidates = os.listdir(os.path.join(config.root, config.match_breaking))
                pool = mp.Pool(config.nb_workers_phase_1)
                # pool.map(process_a_combination,candidates)
                # process_a_combination('39960404_3.csv')
                for _ in tqdm(pool.imap_unordered(Prepare_DataTS.process_a_combination, [(candidate,batch_cus_dict,config) for candidate in candidates]), total=len(candidates), desc='MAIN PROCESS'):
                    pass
                pool.close()
                pool.join()
                # for _ in tqdm(pool.imap_unordered(process_a_combination, [(candidate,cus_dict) for candidate in candidates]), total=len(candidates), desc='MAIN PROCESS'):
                #     pass
                print('\n', '********************************************************************************************************************************************')
                print("\n", f"{ENV} | PROCESSING TIME %.0f SECONDS" %
                    (time.time() - start_processing))
                logging.info(
                    f"{ENV} | Done phase 1, takes {time.time() - start_processing} seconds")
            except Exception as e:
                message_telegram = f"{ENV} | Error phase 1: {e}"
                Function_Support.notify_logging(message_telegram)
                break

            # END PHASE 1 - START PHASE 2
            # *****************************************************************************************************************************************************************************
            check_files = [f for f in sorted(os.listdir(config.root_orig))]
            while len(check_files)==0:
                time.sleep(config.time_sleep)
                check_files = [f for f in sorted(os.listdir(config.root_orig))]
            orig_fn = check_files[0]
            day_curr=orig_fn.split('.')[0].split('_')[2]
            initial.append(day_curr)
            time_constant=int(day_curr)-int(day_prev)
            if time_constant !=0 :
                start_time = time.time()
                the_first_is_the_last = False
                if len(initial)>2:
                    try:
                        start_time = time.time()
                        # read customer list
                        # with open(os.path.join(root, cus_list_fn), 'rb') as f:
                        #     daily_cus_list = pickle.load(f)

                        # build batches
                        batch_cus_list = sorted(batch_cus_list)
                        BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+config.num_batch_cus]]) for x in range(0, len(batch_cus_list), config.num_batch_cus)]
                        # print('First Batch',BATCHES[0],sep='\n')
                        # logging.info(f"number of cust list: {len(batch_cus_list)}")
                        logging.info(f"number of cust list: {len(batch_cus_list)}")
                        pool = mp.Pool(config.nb_workers_phase_2)
                        # result = pool.map(aggregate, [(np.min(BATCH), np.max(BATCH),date_insert,daily_cus_dict) for BATCH in BATCHES])
                        for _ in tqdm(pool.imap_unordered(AggOnTheFly.aggregate,[(BATCH,config,date_insert,daily_cus_dict) for BATCH in BATCHES]),total=len(BATCHES),desc=f'AGG | A BATCH OF {date_insert}'):
                            pass
                        pool.close()
                        pool.join()
                        logging.info(f'A BATCH of {date_insert} done in {time.time()-start_time} seconds')
                        # print(f'Once more batch of {date_insert} overcame phase 2 successfully !')

                    except Exception as e:
                        message_telegram = f"{ENV} | Error phase 2 right before day end: {e}"
                        Function_Support.notify_logging(message_telegram)
                        break
                else:
                    the_first_is_the_last = True
                date_insert=year_prev+'-'+month_prev+'-'+day_prev
                print(f'{ENV} | date_insert when DAY END {date_insert}')
                with open(os.path.join(config.root, config.cus_list_fn), 'rb') as f:
                    daily_cus_list = pickle.load(f)
                with open(os.path.join(config.root, config.cus_dict_fn), 'rb') as g:
                    daily_cus_dict = pickle.load(g)
                daily_cus_list = np.sort(daily_cus_list)
                BATCHES = [daily_cus_list[x:x+config.num_batch_cus] for x in range(0, len(daily_cus_list), config.num_batch_cus)]
                #BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+num_batch_cus]]) for x in range(0, len(batch_cus_list), num_batch_cus)]
                pool = mp.Pool(config.nb_workers_phase_2)
                for _ in tqdm(pool.imap_unordered(AggDayEnd.day_end_aggregate,[(min(BATCH),max(BATCH),config,date_insert,the_first_is_the_last,daily_cus_dict) for BATCH in BATCHES]), total=len(BATCHES), desc='DAY-END AGG'):
                    pass
                pool.close()
                pool.join()
                conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
                cur = conn.cursor()
                # update table SystemParameter
                in1,out1 = cur.callproc('SPU_AIML_UpdateScanStatus',[date_insert, None])
                if out1 is not None:
                    message_telegram = f'{ENV} | Error return from SP SPU_AIML_UpdateScanStatus: {out1}'
                    Function_Support.notify_logging(message_telegram)
                conn.commit()

                cur.close()
                conn.close()
                print("***********************************************************************************************************************************************************************************")
                print("%s | AGG & INSERT TIME %.0f SECONDS" %
                    (ENV,time.time() - start_time))
                message_telegram = f"{ENV} | Group Betting is done, total {round((time.time() - time_begin)/3600,4)} hours "
                Function_Support.notify_logging(message_telegram,True)
                conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                    host=config.aimlhost, port=config.aimlport, database=config.aimldb)
                cur = conn.cursor()
                # Truncate table AssociationStatsStaging
                cur.callproc('SPU_AIML_DBA_Truncate_Table',
                            ['AssociationStatsStaging'])
                conn.commit()
                check_cus_files=os.listdir(config.root)
                if config.cus_list_fn in check_cus_files:
                    os.remove(os.path.join(config.root,config.cus_list_fn))
                if config.cus_dict_fn in check_cus_files:
                    os.remove(os.path.join(config.root,config.cus_dict_fn))
                initial = []
                continue           
            try:
                start_time = time.time()
                # build batches
                batch_cus_list = sorted(batch_cus_list)
                BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+config.num_batch_cus]]) for x in range(0, len(batch_cus_list), config.num_batch_cus)]
                logging.info("*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*")
                logging.info(f"number of cust list: {len(batch_cus_list)}")
                pool = mp.Pool(config.nb_workers_phase_2)
                
                for _ in tqdm(pool.imap_unordered(AggOnTheFly.aggregate,[(BATCH,config,date_insert,daily_cus_dict) for BATCH in BATCHES]), total=len(BATCHES), desc='AGG'):
                    pass
                pool.close()
                pool.join()
                # myls = [item for sublist in bigls for item in sublist]
                # results = pd.DataFrame(myls)
                logging.info(f'{ENV} | Done phase 2, takes {time.time()-start_time} seconds')
                # print(f'Once more batch of {date_insert} overcame phase 2 successfully !')

            except Exception as e:
                message_telegram = f"{ENV} | Error phase 2: {e}"
                Function_Support.notify_logging(message_telegram)
                break
        else:
            time.sleep(config.time_sleep)
    
