import pandas as pd
import numpy as np
import multiprocessing as mp
import logging
import csv
import json
import warnings
from Supporters.Helpers import *
from Supporters.Aggregate import aggregate
from MainJobs.Pairwise import doPhase1
from MainJobs.DayEndAgg import DayEndAgg
from MainJobs.OnTheFlyAgg import OnTheFlyAgg
import re
import datetime
import time
import pickle
import os
import torch

from tqdm import tqdm
from mysql.connector import MySQLConnection
from Configuration.LocalConfiguration import LocalConfiguration
from Configuration.ProConfiguration import ProConfiguration
from datetime import date as dt
from datetime import timedelta

warnings.filterwarnings("ignore")

ENV='LOCAL'

if ENV=='LOCAL':

    config = LocalConfiguration()

else:
    config = ProConfiguration()

# define log config
save_dir_log = config.GetSaveDirectoryLog(config)
log_name = config.GetLogName(config)
logging.basicConfig(filename=os.path.join(
    save_dir_log, log_name), level=logging.INFO)

# define GroupBetting config
config_retry = int(config.getRetry(config))
time_sleep = int(config.getTimeSleep(config))
percent_score = int(config.getPercentScore(config))
combination_threshold = int(config.GetCombinationThreshold(config))
time_threshold = int(config.GetTimeThreshold(config))
# define paths
root=config.GetSaveDataDir(config)
root_orig=config.GetPathCsvFile(config)
orig_fn=config.GetNameFile(config)
match_breaking=config.GetMatchBreaking(config)
cus_list_fn=config.GetListName(config)
cus_dict_fn=config.GetDictName(config)
mlm_dict_fn=config.GetMatchLeagueMap(config)
backup=config.GetBackUp(config)

# define chunk_size for DB saving
chunk_size = int(config.getChunkSize(config))

# define nb_workers_phase_1
nb_workers_phase_1 = int(config.getNumberWorkerPhase1(config))

# define nb_workers_phase_2
nb_workers_phase_2 = int(config.getNumberWorkerPhase2(config))

# define batch size for get customers in phase 2
num_batch_cus = int(config.getNumBatchCus(config))

aimluser=config.getSPU_AIMLUsername(config)
aimlpwd=config.getSPU_AIMLPassword(config)
aimlhost=config.getSPU_AIMLHost(config)
aimlport=config.getSPU_AIMLPort(config)
aimldb=config.getSPU_AIMLDatabaseName(config)

ctsuser=config.getCTS_DataCenterUsername(config)
ctspwd=config.getCTS_DataCenterPassword(config)
ctshost=config.getCTS_DataCenterHost(config)
ctsport=config.getCTS_DataCenterPort(config)
ctsdb=config.getCTS_DataCenterDatabaseName(config)

# define is transfer data to CTS
transfer_score = config.getTransferDataScore(config)
transfer_ip = config.getTransferDataIP(config)


if __name__ == "__main__":
    conn = MySQLConnection(user=aimluser, password=aimlpwd,
                            host=aimlhost, port=aimlport, database=aimldb)
    cur = conn.cursor()
    # Truncate table AssociationStatsStaging
    cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
                ['AssociationStatsStaging'])
    cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
                ['AssociationSuspiciousInfo'])
    cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
                ['AssociationStats'])
    # cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
    #             ['AssociationByAI'])
    conn.commit()
    check_cus_files=os.listdir(root)
    if cus_list_fn in check_cus_files:
        os.remove(os.path.join(root,cus_list_fn))
    if cus_dict_fn in check_cus_files:
        os.remove(os.path.join(root,cus_dict_fn))
    initial = []
    while True:
        check_files = [f for f in sorted(os.listdir(root_orig))]
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
                # today = dt.today()
                # logging.info(
                #     "======================================================================================================")
                # logging.info(f"{ENV} | Running for Date: {year_prev+'-'+month_prev+'-'+day_prev}")
                print("======================================================================================================")
                print(f"{ENV} | Running for Date: {year_prev+'-'+month_prev+'-'+day_prev}")
                print('day_prev {0}'.format(day_prev))
                # message_telegram = f"{ENV} | Group Betting is running for {year_prev+'-'+month_prev+'-'+day_prev}"
                # SendLogTelegram.send_message(message_telegram)
                initial.append(day_prev)
            

            # START PHASE 0 --> PREPARATION
            # *****************************************************************************************************************************************************************************
            try:
                time_phase0 = time.time()
                t = time.localtime()
                current_time = time.strftime("%H:%M:%S", t)
                # print(f"{ENV} | CURRENT TIME : ", current_time)

                # read - filter - preprocess data
                data = recursiveApp(check_files_sameday)
                if len(data.index)==0 or data.bettype.isnull().values.any():
                    os.remove(os.path.join(root_orig, orig_fn))
                    continue
                DATE = data[(data.bettype.isin([1, 3, 7, 8]))
                            & (data.liveindicator)]
                if len(DATE.index)==0:
                    os.remove(os.path.join(root_orig, orig_fn))
                    continue

                date_winlost = DATE['winlostdate'].min()
                DATE['category'] = DATE['category'].fillna(value='minor')
                DATE['category'] = DATE['category'].str.lower()
                DATE = DATE[['custid', 'matchid', 'transdate', 'bettype','leagueid','category']]
                date = DATE['transdate'].min()
                date_insert = date_winlost.split()[0]
                # date_insert='2021-01-29'
                # print(f"date insert {date_insert}")
                DATE['transdate'] = DATE['transdate'].apply(
                    lambda z: distance_time(separate(date), separate(z)))

                # get list of matches
                matches = DATE.matchid.unique()
                # print(f'Number of matches {len(matches)}')

                # get list of custid
                batch_cus_list = list(DATE.custid.unique())
                check_cus_files=os.listdir(os.path.join(root))
                if cus_list_fn not in check_cus_files:
                    with open(os.path.join(root, cus_list_fn), 'wb') as f:
                        pickle.dump(batch_cus_list, f)
                else:
                    with open(os.path.join(root, cus_list_fn), 'rb') as f:
                        daily_cus_list = pickle.load(f)
                    daily_cus_list+=batch_cus_list
                    daily_cus_list=list(set(daily_cus_list))
                    with open(os.path.join(root, cus_list_fn), 'wb') as f:
                        pickle.dump(daily_cus_list, f)

                # match breaking
                check_match_files=os.listdir(os.path.join(root, match_breaking))
                if len(check_match_files)>0:
                    for fn in check_match_files:
                        os.remove(os.path.join(root, match_breaking,fn))
                # for n in tqdm(range(len(matches)), desc="MATCH BREAKING"):
                for n in range(len(matches)):
                    match = matches[n]
                    m = DATE[DATE.matchid == match]
                    for bt in [1, 3, 7, 8]:
                        f = m[m.bettype == bt]
                        if f.custid.nunique() > 1:
                            f.to_csv(os.path.join(root, match_breaking,
                                                f"{match}_{bt}.csv"), index=False)

                del DATE, data
                print('\n')

                # build batch_cus_dict for count joining combinations
                batch_cus_dict = {}
                ls_mat = os.listdir(os.path.join(root, match_breaking))
                # for k in tqdm(range(len(ls_mat)), desc="BUILD CUS DICT"):
                for k in range(len(ls_mat)):
                    fn = ls_mat[k]
                    match, bt = int(fn.split('.')[0].split('_')[0]), int(
                        fn.split('.')[0].split('_')[1])
                    df = pd.read_csv(os.path.join(root, match_breaking, fn))

                    ls = df.custid.unique()
                    for cus in ls:
                        if cus not in batch_cus_dict:
                            batch_cus_dict[cus] = [(match, bt)]
                        else:
                            batch_cus_dict[cus].append((match, bt))
                if cus_dict_fn not in check_cus_files:
                    with open(os.path.join(root, cus_dict_fn), 'wb') as g:
                        pickle.dump(batch_cus_dict, g)
                else:
                    with open(os.path.join(root, cus_dict_fn), 'rb') as g:
                        daily_cus_dict = pickle.load(g)
                    for key,value in batch_cus_dict.items():
                        if key not in daily_cus_dict:
                            daily_cus_dict[key]=value
                        else:
                            daily_cus_dict[key]+=value
                    with open(os.path.join(root, cus_dict_fn), 'wb') as g:
                        pickle.dump(daily_cus_dict, g)
                # print('\n', f"LEN OF CUS DICT {len(batch_cus_dict)}")
                with open(os.path.join(root, cus_dict_fn), 'rb') as g:
                        daily_cus_dict = pickle.load(g)
                # logging.info(
                #     f"{ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
                print(f"{ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
                # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
            except Exception as e:
                # logging.error(f"{ENV} | Error at phase 0: {e}")
                print(f"{ENV} | Error at phase 0: {e}")
                # message_telegram = f"{ENV} | Error at phase 0: {e}"
                # SendLogTelegram.send_message(message_telegram)
                break

            # END PHASE 0 - START PHASE 1
            # ****************************************************************************************************************************************************************************
            try:
                start_processing = time.time()

                candidates = os.listdir(os.path.join(root, match_breaking))
                pool = mp.Pool(nb_workers_phase_1)
                # pool.map(process_a_combination,candidates)
                # process_a_combination('39960404_3.csv')
                # for _ in tqdm(pool.imap_unordered(process_a_combination, candidates), total=len(candidates), desc='MAIN PROCESS'):
                #     pass
                for _ in tqdm(pool.imap_unordered(doPhase1, [(candidate,batch_cus_dict) for candidate in candidates]), total=len(candidates), desc=f'PAIRWISE | A BATCH OF {date_insert}'):
                    pass
                # list_of_cus_list = list(tqdm(pool.imap(process_a_combination, [(candidate,batch_cus_dict) for candidate in candidates]),total=len(candidates),desc=f'PAIRWISE {orig_fn}'))
                # batch_cus_list = [item for sublist in list_of_cus_list for item in sublist]
                # batch_cus_list = list(set(batch_cus_list))
                pool.close()
                pool.join()
                # print('\n', '********************************************************************************************************************************************')
                # print("\n", f"{ENV} | PROCESSING TIME %.0f SECONDS" %
                    # (time.time() - start_processing))
                # logging.info(
                #     f"{ENV} | Done phase 1, takes {time.time() - start_processing} seconds")
                print(f"{ENV} | Done phase 1, takes {time.time() - start_processing} seconds")
            except Exception as e:
                # logging.error(f"{ENV} | Error phase 1: {e}")
                print(f"{ENV} | Error phase 1: {e}")
                # message_telegram = f"{ENV} | Error phase 1: {e}"
                # SendLogTelegram.send_message(message_telegram)
                break

            # END PHASE 1 - START PHASE 2
            # *****************************************************************************************************************************************************************************
            check_files = [f for f in sorted(os.listdir(root_orig))]
            while len(check_files)==0:
                time.sleep(time_sleep)
                check_files = [f for f in sorted(os.listdir(root_orig))]
            orig_fn = check_files[0]
            # month_curr=orig_fn.split('.')[0].split('_')[1]
            day_curr=orig_fn.split('.')[0].split('_')[2]
            initial.append(day_curr)
            # year_curr=orig_fn.split('.')[0].split('_')[3]
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
                        BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+num_batch_cus]]) for x in range(0, len(batch_cus_list), num_batch_cus)]
                        # print('First Batch',BATCHES[0],sep='\n')
                        # logging.info(f"number of cust list: {len(batch_cus_list)}")
                        print(f"number of cust list: {len(batch_cus_list)}")
                        pool = mp.Pool(nb_workers_phase_2)
                        # result = pool.map(aggregate, [(np.min(BATCH), np.max(BATCH),date_insert,daily_cus_dict) for BATCH in BATCHES])
                        for _ in tqdm(pool.imap_unordered(OnTheFlyAgg, [(BATCH,date_insert,daily_cus_dict) for BATCH in BATCHES]),total=len(BATCHES),desc=f'AGG | A BATCH OF {date_insert}'):
                            pass
                        pool.close()
                        pool.join()
                        print(f'A BATCH of {date_insert} done in {time.time()-start_time} seconds')
                        # print(f'Once more batch of {date_insert} overcame phase 2 successfully !')

                    except Exception as e:
                        # logging.error(f"{ENV} | Error phase 2: {e}")
                        print(f"{ENV} | Error phase 2: {e}")
                        # message_telegram = f"{ENV} | Error phase 2: {e}"
                        # SendLogTelegram.send_message(message_telegram)
                        break
                else:
                    the_first_is_the_last = True
                date_insert=year_prev+'-'+month_prev+'-'+day_prev
                print(f'{ENV} | date_insert when DAY END {date_insert}')
                with open(os.path.join(root, cus_list_fn), 'rb') as f:
                    daily_cus_list = pickle.load(f)
                with open(os.path.join(root, cus_dict_fn), 'rb') as g:
                    daily_cus_dict = pickle.load(g)
                daily_cus_list = sorted(daily_cus_list)
                BATCHES = [daily_cus_list[x:x+num_batch_cus] for x in range(0, len(daily_cus_list), num_batch_cus)]
                # BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+num_batch_cus]]) for x in range(0, len(batch_cus_list), num_batch_cus)]
                pool = mp.Pool(nb_workers_phase_2)
                for _ in tqdm(pool.imap_unordered(DayEndAgg, [(min(BATCH),max(BATCH),date_insert,daily_cus_dict,the_first_is_the_last) for BATCH in BATCHES])
                                                , total=len(BATCHES), desc='DAY-END AGG'):
                    pass
                pool.close()
                pool.join()
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                # update table SystemParameter
                # cur.callproc('SPU_AIML.SPU_AIML_UpdateScanStatus',
                #             [date_insert, None])
                in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_UpdateScanStatus',[date_insert, None])
                if out1 is not None:
                    print(out1)
                    # logging.error(f'{ENV} | Error return from SP SPU_AIML_UpdateScanStatus: {out1}')
                    # message_telegram = f'{ENV} | Error return from SP SPU_AIML_UpdateScanStatus: {out1}'
                    # SendLogTelegram.send_message(message_telegram)
                conn.commit()

                cur.close()
                conn.close()
                print("***********************************************************************************************************************************************************************************")
                print("%s | AGG & INSERT TIME %.0f SECONDS" %
                    (ENV,time.time() - start_time))
                # logging.info(
                #     f"{ENV} | Done day-end phase 2, takes {time.time() - start_time} seconds")
                print(f"{ENV} | Done day-end phase 2, takes {time.time() - start_time} seconds")
                # message_telegram = f"{ENV} | Group Betting is done, total {round((time.time() - time_begin)/3600,4)} hours "
                # SendLogTelegram.send_message(message_telegram)
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                # Truncate table AssociationStatsStaging
                cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
                            ['AssociationStatsStaging'])
                conn.commit()
                check_cus_files=os.listdir(root)
                if cus_list_fn in check_cus_files:
                    os.remove(os.path.join(root,cus_list_fn))
                if cus_dict_fn in check_cus_files:
                    os.remove(os.path.join(root,cus_dict_fn))
                initial = []
                continue
            else:           
                try:
                    start_time = time.time()
                    # read customer list
                    # with open(os.path.join(root, cus_list_fn), 'rb') as f:
                    #     daily_cus_list = pickle.load(f)

                    # build batches
                    batch_cus_list = sorted(batch_cus_list)
                    BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+num_batch_cus]]) for x in range(0, len(batch_cus_list), num_batch_cus)]
                    # print('First Batch',BATCHES[0],sep='\n')
                    # logging.info(f"number of cust list: {len(batch_cus_list)}")
                    print(f"number of cust list: {len(batch_cus_list)}")
                    pool = mp.Pool(nb_workers_phase_2)
                    # result = pool.map(aggregate, [(np.min(BATCH), np.max(BATCH),date_insert,daily_cus_dict) for BATCH in BATCHES])
                    for _ in tqdm(pool.imap_unordered(OnTheFlyAgg, [(BATCH,date_insert,daily_cus_dict) for BATCH in BATCHES]),total=len(BATCHES),desc=f'AGG | A BATCH OF {date_insert}'):
                        pass
                    pool.close()
                    pool.join()
                    print(f'A BATCH of {date_insert} done in {time.time()-start_time} seconds')
                    # print(f'Once more batch of {date_insert} overcame phase 2 successfully !')

                except Exception as e:
                    # logging.error(f"{ENV} | Error phase 2: {e}")
                    print(f"{ENV} | Error phase 2: {e}")
                    # message_telegram = f"{ENV} | Error phase 2: {e}"
                    # SendLogTelegram.send_message(message_telegram)
                    break
                    
            # remove file when complete
            # os.remove(os.path.join(root_orig,orig_fn))
            # os.rename(os.path.join(root_orig,orig_fn),os.path.join(backup,orig_fn))
        
        else:
            time.sleep(time_sleep)
    
