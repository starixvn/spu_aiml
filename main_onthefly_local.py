import pandas as pd
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
import logging
import csv
import json
import warnings
from GroupBetting import helper
from GroupBetting import SendLogTelegram
# import SendLogTelegram
# import agg
import datetime
import time
import pickle
import itertools
import gc
import os
import torch

from tqdm import tqdm
# from pandarallel import pandarallel
# from sklearn.metrics import pairwise_distances
from mysql.connector import MySQLConnection
from Configuration.LocalConfiguration import LocalConfiguration
from Configuration.ProConfiguration import ProConfiguration
from datetime import date as dt
from datetime import timedelta

warnings.filterwarnings("ignore")

ENV='LOCAL'

if ENV=='LOCAL':

    config = LocalConfiguration()

    # define log config
    save_dir_log = config.GetSaveDirectoryLog(config)
    log_name = config.GetLogName(config)
    logging.basicConfig(filename=os.path.join(
        save_dir_log, log_name), level=logging.INFO)

    # define GroupBetting config
    config_retry = int(config.getRetry(config))
    time_sleep = int(config.getTimeSleep(config))
    percent_score = int(config.getPercentScore(config))
    time_threshold = int(config.GetTimeThreshold(config))
    combination_threshold = int(config.GetCombinationThreshold(config))
    # define paths
    root=config.GetSaveDataDir(config)
    root_orig=config.GetPathCsvFile(config)
    orig_fn=config.GetNameFile(config)
    match_breaking=config.GetMatchBreaking(config)
    cus_list_fn=config.GetListName(config)
    cus_dict_fn=config.GetDictName(config)
    mlm_dict_fn=config.GetMatchLeagueMap(config)


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
    time_threshold = int(config.GetTimeThreshold(config))
    combination_threshold = int(config.GetCombinationThreshold(config))
    # define paths
    root=config.GetSaveDataDir(config)
    root_orig=config.GetPathCsvFile(config)
    orig_fn=config.GetNameFile(config)
    match_breaking=config.GetMatchBreaking(config)
    cus_list_fn=config.GetListName(config)
    cus_dict_fn=config.GetDictName(config)
    mlm_dict_fn=config.GetMatchLeagueMap(config)


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

def separate(transdate):
    """
    >>> Input  :    '2020-09-26 7:31:01.872'

    >>> Output :    (2020,9,26,7,31,1)
    """
    date, hms = transdate.split(' ')[0].split(
        '-'), transdate.split(' ')[1].split('.')[0].split(':')
    year, month, day = int(date[0]), int(date[1]), int(date[2])
    hour, min, sec = int(hms[0]), int(hms[1]), int(hms[2])
    return (year, month, day, hour, min, sec)


def distance_time(transdate1, transdate2):
    """
    >>> Input  : transdate 1 : datetime.datetime(2020,9,26,7,28,1)

                 transdate 2 : datetime.datetime(2020,9,26,7,31,1)

    >>> Output : 180 seconds
    """

    return (datetime.datetime(*transdate2)-datetime.datetime(*transdate1)).total_seconds()


def process_a_combination(args):
    """
    >>> Input    :  filepath,cus_dict
    >>> Output   :  pairwise-time-score matrix
    """
    filepath,cus_dict=args[0],args[1]
    # get match - bettype - league
    match = int(filepath.split('.')[0].split('_')[0])
    bettype = int(filepath.split('.')[0].split('_')[1])

    # read data of a (match,bettype) - combination
    MATCH = pd.read_csv(os.path.join(root, match_breaking, filepath))

    # pick up customer list and sort it
    CUST_LIST = np.sort(MATCH.custid.unique())

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
    # for j in tqdm(range(len(CUST_LIST)),desc=f"M {match} B {bettype} | {len(CUST_LIST)} CUSTOMERS | TRASH ADDING. . ."):
    for j in range(len(CUST_LIST)):
        val = MATCH[MATCH['custid'] == CUST_LIST[j]][[
            'transdate', 'custid']].values.flatten()
        val = np.pad(val, (0, maxlen*2-len(val)),
                     'constant', constant_values=-1)
        X.append(val)
    X = np.asarray(X)

    # compute pairwise-time-score matrix
    start_compute = time.time()
    m = helper.compute_pairwise_cus(X, time_threshold)
    #print("\n","PAIRWISE MATRIX HAVING SHAPE %s OF MATCH %.0f BETTYPE %.0f :" % (m.shape,match,bettype),m,sep='\n')
    print("\n", "MATCH %.0f BETTYPE %.0f HAVING SHAPE %.0f COMPUTING TIME SCORE TAKES %.0f SECONDS" % (
        match, bettype, len(CUST_LIST), time.time() - start_compute))
    del X, MATCH
    gc.collect()

    # build up result object which is a list of dictionaries whose values are positive time score
    start_transform = time.time()

    obj = [

        {"C1": int(CUST_LIST[i]), "C2":int(CUST_LIST[j]), "TS": m[i, j], "M":match, "B":bettype
            , "L":int(leagueid)
            , "TJC":count_joining_combs(CUST_LIST[i], CUST_LIST[j],cus_dict)
            , "IML":IMJ
            ,  "IN":1}

        for (i, j) in itertools.combinations([x for x in range(len(CUST_LIST))], 2) if m[i, j] > 0
    ]
    # print(f"JSON OBJ 1th {obj[0]}",f"JSON OBJ 2nd {obj[1]}",f"JSON OBJ 3rd {obj[2]}",sep='\n')

    start_save = time.time()
    # build chunks for DB saving
    chunks = [obj[x:x+chunk_size] for x in range(0, len(obj), chunk_size)]
    del m
    #print("JSON OBJECT :",obj,sep="\n")
    print("\n", "MATCH %.0f BETTYPE %.0f HAVING SHAPE %.0f TRANSFROMING TAKES %.0f SECONDS" % (
        match, bettype, len(CUST_LIST), time.time() - start_transform))

    # filter json obj
    if len(obj) > 0:
        try:
            conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                   host=aimlhost, port=aimlport, database=aimldb)
            cursor = conn.cursor()
            for chunk in chunks:
                jsonList = json.dumps(chunk)
                cursor.callproc(
                    'SPU_AIML_InsertAssociationStatsStaging', [jsonList, None])
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    print("\n", "MATCH %.0f BETTYPE %.0f HAVING SHAPE %.0f SAVING TAKES %.0f SECONDS" % (
        match, bettype, len(CUST_LIST), time.time() - start_save))
    del chunks, obj
    gc.collect()


def count_joining_combs(cus1, cus2,cus_dict):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(cus_dict[cus1]), set(cus_dict[cus2])
    return len(comb_a.intersection(comb_b))

def transform_to_list(df):
    keys, values1, values2 = df.sort_values('sample_id').values.T
    ukeys, index = np.unique(keys, True)
    arrays = np.split(values1, index[1:])
    arrays2 = np.split(values2, index[1:])
    df2 = pd.DataFrame({'sample_id': ukeys, 'ML': [list(
        a) for a in arrays], 'BL': [list(b) for b in arrays2]})
    return df2


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

    return 1 - sum(map(lambda x: (x/sum_match)**2, lista))

def total_leaguescore(x, y):
    if y == 1:
        return (x + 5/2) * (2/7)
    elif x == 1:
        return (y + 3/2) * (2/5)
    elif y != 1 and x != 1:
        minor_score = (x + 5/2) * (2/7)
        major_score = (y + 3/2) * (2/5)
        return (3 * (minor_score + 1) + (major_score + 2)) * (1/9)

def day_end_aggregate(args):
    try:
        results,date_insert=pd.DataFrame(args[2]),args[3]
        sub_results=results[(results.C1>=int(args[0]))&(results.C1<=int(args[1]))]
        conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
        cur = conn.cursor()
        cur.callproc('SPU_AIML_GetAssociationStats',
                    [int(args[0]), int(args[1]), None])
        dba_results = [r.fetchall() for r in cur.stored_results()]
        conn.commit()
        cur.close()
        conn.close()

        if len(dba_results[0]) == 0:
            return True
        df = pd.DataFrame(dba_results[0], columns=[
            "C1",
            "C2",
            "TS",
            "ML",
            "BL",
            "LeagueID",
            "IsMajorLeague",
            "TJC",
            "IsNew",
            "AccTS",
            "AccMS",
            "AccLS",
            "AccTJD"
            ])
        # fill 0 to NaN
        df['AccTS'].fillna(0, inplace=True)
        df['AccMS'].fillna(0, inplace=True)
        df['AccLS'].fillna(0, inplace=True)
        df['AccTJD'].fillna(0, inplace=True)

        df['TS'] = df['TS'].astype('float')
        df['AccTS'] = df['AccTS'].astype('float')
        df['AccMS'] = df['AccMS'].astype('float')
        df['AccLS'] = df['AccLS'].astype('float')

        df=df[['C1','C2','AccTS','AccMS','AccLS','AccTJD']]
        
        df=df.drop_duplicates()

        df_DailyScore=pd.merge(df,sub_results,how='left',left_on=['C1','C2'],right_on=['C1','C2'])

        df_DailyScore['AccTS'] = df_DailyScore['AccTS'] + df_DailyScore['TS']

        df_DailyScore['AccMS'] = df_DailyScore['AccMS'] + df_DailyScore['MS']

        df_DailyScore['AccLS'] = df_DailyScore['AccLS'] + df_DailyScore['LS']
    
        df_DailyScore['AccTJD'] += 1

        df_DailyScore['BC']=1
        
        df_result3=df_DailyScore[['C1','C2','AccTS','AccMS','AccLS','AccTJD','TJC','TJSC','BC']]
        df_result3.rename(columns={'AccTS':'TS','AccMS':'MS','AccLS':'LS','AccTJD':'TJD'},inplace=True)
    

        df_DailyScore['S'] = 100 * (df_DailyScore['AccTS'] + df_DailyScore['AccMS'] +
                                    df_DailyScore['AccLS']) / 3


        df_byAISample01 = df_DailyScore['TJSC']
        df_byAISample02 = df_DailyScore[['C1', 'C2', 'S']]
        df_byAISample03 = pd.merge(
            df_byAISample02, df_byAISample01, left_index=True, right_index=True)
        df_byAI = df_byAISample03[(df_byAISample03['S'] >= percent_score) & (
            df_byAISample03['TJSC'] >= combination_threshold)]
                
        isTraceLog = False
        df_byAISPU = pd.DataFrame()
        if len(df_byAI.index) != 0:
            isTraceLog = True
            df_result4 = df_result3[['TS', 'MS', 'LS', 'TJD', 'TJC']]
            df_byAISPU = pd.merge(df_result4, df_byAI,
                                left_index=True, right_index=True)

        # move to dba
        fulldata_dba = df_result3.to_dict(orient="records")
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")
        fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")


        chunks1 = [fulldata_dba[x:x+chunk_size]
                for x in range(0, len(fulldata_dba), chunk_size)]

        chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                for x in range(0, len(fulldatabyAI_dba), chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
                for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]   

        try:
            conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                host=aimlhost, port=aimlport, database=aimldb)
            cur = conn.cursor()
            if isTraceLog:
                for (chunk1, chunk5) in zip(chunks1, chunks5):
                    json_obj1 = json.dumps(chunk1)
                    cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationStats', [
                                json_obj1, date_insert, None])
                    conn.commit()

                    json_obj5 = json.dumps(chunk5)
                    cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [
                                    json_obj5, None])
                    conn.commit()
                    
            else:
                for chunk1 in chunks1:
                    json_obj1 = json.dumps(chunk1)
                    cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationStats', [
                                json_obj1, date_insert, None])
                    conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
            # message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError

        # insert dba CTS
        try:
            conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                host=ctshost, port=ctsport, database=ctsdb)
            cur = conn.cursor()
            for chunk4 in chunks4:
                json_obj4 = json.dumps(chunk4)
                cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [
                            json_obj4, date_insert, None])
                conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
            # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    except Exception as err:
        logging.error(f'{ENV} | Error in day-end agg function: {err}')
        # message_telegram = f'{ENV} | Error in day-end agg function: {err}'
        # SendLogTelegram.send_message(message_telegram)
        raise ValueError

def aggregate(args):
    try:
        date_insert,daily_cus_dict=args[2],args[3]
        conn = MySQLConnection(user=aimluser, password=aimlpwd,
                            host=aimlhost, port=aimlport, database=aimldb)
        cur = conn.cursor()
        cur.callproc('SPU_AIML_GetAssociationStatsStaging',
                    [int(args[0]), int(args[1]), None])
        dba_results = [r.fetchall() for r in cur.stored_results()]
        conn.commit()
        cur.close()
        conn.close()
        if len(dba_results[0]) == 0:
            return []
        df = pd.DataFrame(dba_results[0], columns=[
            "C1",
            "C2",
            "TS",
            "ML",
            "BL",
            "LeagueID",
            "IsMajorLeague",
            "TJC",
            "IsNew"
            ])
        IsNewdf=df[df.IsNew==1]
        if len(IsNewdf)>0:
            IsNewdf['sample_id'] = IsNewdf['C1'].map(str) + IsNewdf['C2'].map(str)
            IsNewdf = IsNewdf.astype({"sample_id": 'int64'})
            IsNewdf['TS'] = IsNewdf['TS'].astype('float')
            df_custid = pd.DataFrame()
            df_custid = IsNewdf.groupby('sample_id')[['C1', 'C2', 'TJC']].first()
            df_parameter = (IsNewdf.groupby(['sample_id', 'IsMajorLeague', 'LeagueID']).size(
            ).unstack('IsMajorLeague', fill_value=0))
            df_parameter = df_parameter.reset_index()
            df_parameter2 = (IsNewdf.groupby(['sample_id', 'IsMajorLeague']).size().unstack(
                'IsMajorLeague', fill_value=0))
            df_parameter2 = df_parameter2.reset_index()
            df_parameter3 = pd.merge(df_parameter, df_parameter2, on=['sample_id'])
            if '1_x' not in df_parameter3:
                df_parameter3['1_x'] = 0
                df_parameter3['1_y'] = 0
            if '0_x' not in df_parameter3:
                df_parameter3['0_x'] = 0
                df_parameter3['0_y'] = 0
            df_parameter3 = df_parameter3.rename({
                            '0_x': 'each_league_0',
                            '0_y': 'total_league_0',
                            '1_x': 'each_league_1',
                            '1_y': 'total_league_1'
                        }, axis=1)
            df_parameter3['score_eachleague_0'] = [(x/y)**2 if y != 0 else 0 for x, y in zip(
                df_parameter3['each_league_0'], df_parameter3['total_league_0'])]
            df_parameter3['score_eachleague_1'] = [(x/y)**2 if y != 0 else 0 for x, y in zip(
                df_parameter3['each_league_1'], df_parameter3['total_league_1'])]
            df_leaguescore = pd.DataFrame()
            df_leaguescore['minor'] = 1 - \
                df_parameter3.groupby('sample_id')['score_eachleague_0'].sum()
            df_leaguescore['major'] = 1 - \
                df_parameter3.groupby('sample_id')['score_eachleague_1'].sum()
            df_leaguescore['LS'] = df_leaguescore.apply(
                lambda x: total_leaguescore(x['minor'], x['major']), axis=1)
            df_timescore = IsNewdf.groupby('sample_id')[['TS']].mean()
            df_matchscore = pd.DataFrame()
            df_matchscore['TJSC'] = IsNewdf.groupby(['sample_id', 'ML'])[
                'BL'].nunique().groupby('sample_id').sum()
            df_matchscore['MS'] = df_matchscore['TJSC'] / df_custid['TJC']
            df_result = pd.merge(df_custid, df_timescore,
                                left_index=True, right_index=True)
            df_result2 = pd.merge(df_result, df_matchscore,
                                left_index=True, right_index=True)
            # print(df_result2.head())
            df_result3 = pd.merge(df_result2, df_leaguescore,
                                left_index=True, right_index=True)
            susinfo = IsNewdf[['sample_id', 'ML', 'BL']]
            df_susinfo = transform_to_list(susinfo)
            df_susinfo = df_susinfo.set_index('sample_id')
            df_susinfo['ML'] = [','.join(map(str, l)) for l in df_susinfo['ML']]
            df_susinfo['BL'] = [','.join(map(str, l)) for l in df_susinfo['BL']]
            df_resultinfo = pd.merge(
                df_custid, df_susinfo, left_index=True, right_index=True)
            df_result3 = df_result3.drop(columns=['minor', 'major'])
            df_result3['BC'] = 1
            df_resultinfo = df_resultinfo.drop(columns=['TJC'])
            df_sampleDailyScore = IsNewdf[['sample_id', 'C1','C2']]
            df_DailyScore = df_sampleDailyScore.groupby('sample_id').first()
            df_DailyScore['TS'] = df_result3['TS']
            df_DailyScore['MS'] = df_result3['MS']
            df_DailyScore['LS'] = df_result3['LS']
            df_DailyScore['S'] = 100 * (df_DailyScore['TS'] + df_DailyScore['MS'] +
                                                    df_DailyScore['LS']) / 3
            df_byAISample01 = df_result3['TJSC']
            df_byAISample02 = df_DailyScore[['C1', 'C2', 'S']]
            df_byAISample03 = pd.merge(
                df_byAISample02, df_byAISample01, left_index=True, right_index=True)
            df_byAI = df_byAISample03[(df_byAISample03['S'] >= percent_score) & (
                df_byAISample03['TJSC'] >= combination_threshold)]
            isTraceLog = False
            df_byAISPU = pd.DataFrame()
            df_result3['TJD']=1
            if len(df_byAI.index) != 0:
                isTraceLog = True
                df_result4 = df_result3[['TS', 'MS', 'LS', 'TJD', 'TJC']]
                df_byAISPU = pd.merge(df_result4, df_byAI,
                                    left_index=True, right_index=True)
            # move to dba
            fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")


            chunks2 = [fulldatainfo_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatainfo_dba), chunk_size)]


            chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]
            
            try:
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                if isTraceLog:
                    for (chunk2, chunk5) in zip(chunks2, chunks5):

                        json_obj2 = json.dumps(chunk2)
                        cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
                                    json_obj2, None])
                        conn.commit()
                        
                        json_obj5 = json.dumps(chunk5)
                        cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [
                                        json_obj5, None])
                        conn.commit()
                else:
                    for chunk2 in chunks2:
                        json_obj2 = json.dumps(chunk2)
                        cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
                                    json_obj2, None])
                        conn.commit()
                cur.close()
                conn.close()
            except Exception as err:
                logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
                # message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
            
            # insert dba CTS
            try:
                conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                    host=ctshost, port=ctsport, database=ctsdb)
                cur = conn.cursor()
                for chunk4 in chunks4:
                    json_obj4 = json.dumps(chunk4)
                    cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [
                                json_obj4, date_insert, None])
                    conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
            
            # update Staging Status
            try:
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [
                            int(args[0]), int(args[1]), None])
                conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                logging.error(f'{ENV} | Error Update Staging Status: {err}')
                # message_telegram = f'{ENV} | Error Update Staging Status: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
        if len(df)>len(IsNewdf):
            df['TJC']=df.apply(lambda z : count_joining_combs(z['C1'],z['C2'],daily_cus_dict),axis=1)
            df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
            df = df.astype({"sample_id": 'int64'})
            df['TS'] = df['TS'].astype('float')
            df_custid = pd.DataFrame()
            df_custid = df.groupby('sample_id')[['C1', 'C2', 'TJC']].first()
            df_parameter = (df.groupby(['sample_id', 'IsMajorLeague', 'LeagueID']).size(
            ).unstack('IsMajorLeague', fill_value=0))
            df_parameter = df_parameter.reset_index()
            df_parameter2 = (df.groupby(['sample_id', 'IsMajorLeague']).size().unstack(
                'IsMajorLeague', fill_value=0))
            df_parameter2 = df_parameter2.reset_index()
            df_parameter3 = pd.merge(df_parameter, df_parameter2, on=['sample_id'])
            if '1_x' not in df_parameter3:
                df_parameter3['1_x'] = 0
                df_parameter3['1_y'] = 0
            if '0_x' not in df_parameter3:
                df_parameter3['0_x'] = 0
                df_parameter3['0_y'] = 0
            df_parameter3 = df_parameter3.rename({
                            '0_x': 'each_league_0',
                            '0_y': 'total_league_0',
                            '1_x': 'each_league_1',
                            '1_y': 'total_league_1'
                        }, axis=1)
            df_parameter3['score_eachleague_0'] = [(x/y)**2 if y != 0 else 0 for x, y in zip(
                df_parameter3['each_league_0'], df_parameter3['total_league_0'])]
            df_parameter3['score_eachleague_1'] = [(x/y)**2 if y != 0 else 0 for x, y in zip(
                df_parameter3['each_league_1'], df_parameter3['total_league_1'])]
            df_leaguescore = pd.DataFrame()
            df_leaguescore['minor'] = 1 - \
                df_parameter3.groupby('sample_id')['score_eachleague_0'].sum()
            df_leaguescore['major'] = 1 - \
                df_parameter3.groupby('sample_id')['score_eachleague_1'].sum()
            df_leaguescore['LS'] = df_leaguescore.apply(
                lambda x: total_leaguescore(x['minor'], x['major']), axis=1)
            df_timescore = df.groupby('sample_id')[['TS']].mean()
            df_matchscore = pd.DataFrame()
            df_matchscore['TJSC'] = df.groupby(['sample_id', 'ML'])[
                'BL'].nunique().groupby('sample_id').sum()
            df_matchscore['MS'] = df_matchscore['TJSC'] / df_custid['TJC']
            df_result = pd.merge(df_custid, df_timescore,
                                left_index=True, right_index=True)
            df_result2 = pd.merge(df_result, df_matchscore,
                                left_index=True, right_index=True)
            df_result3 = pd.merge(df_result2, df_leaguescore,
                                left_index=True, right_index=True)
            susinfo = df[['sample_id', 'ML', 'BL']]
            df_susinfo = transform_to_list(susinfo)
            df_susinfo = df_susinfo.set_index('sample_id')
            df_susinfo['ML'] = [','.join(map(str, l)) for l in df_susinfo['ML']]
            df_susinfo['BL'] = [','.join(map(str, l)) for l in df_susinfo['BL']]
            df_resultinfo = pd.merge(
                df_custid, df_susinfo, left_index=True, right_index=True)
            df_result3 = df_result3.drop(columns=['minor', 'major'])
            df_result3['BC'] = 1
            df_resultinfo = df_resultinfo.drop(columns=['TJC'])
            df_sampleDailyScore = df[['sample_id', 'C1','C2']]
            df_DailyScore = df_sampleDailyScore.groupby('sample_id').first()
            df_DailyScore['TS'] = df_result3['TS']
            df_DailyScore['MS'] = df_result3['MS']
            df_DailyScore['LS'] = df_result3['LS']
            df_DailyScore['S'] = 100 * (df_DailyScore['TS'] + df_DailyScore['MS'] +
                                                    df_DailyScore['LS']) / 3
            df_byAISample01 = df_result3['TJSC']
            df_byAISample02 = df_DailyScore[['C1', 'C2', 'S']]
            df_byAISample03 = pd.merge(
                df_byAISample02, df_byAISample01, left_index=True, right_index=True)
            df_byAI = df_byAISample03[(df_byAISample03['S'] >= percent_score) & (
                df_byAISample03['TJSC'] >= combination_threshold)]
            isTraceLog = False
            df_byAISPU = pd.DataFrame()
            df_result3['TJD']=1
            if len(df_byAI.index) != 0:
                isTraceLog = True
                df_result4 = df_result3[['TS', 'MS', 'LS', 'TJD', 'TJC']]
                df_byAISPU = pd.merge(df_result4, df_byAI,
                                    left_index=True, right_index=True)
            # move to dba
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")

            chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]
        
            try:
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                if isTraceLog:
                    for chunk5 in chunks5:                     
                        json_obj5 = json.dumps(chunk5)
                        cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [
                                        json_obj5, None])
                        conn.commit()
                cur.close()
                conn.close()
            except Exception as err:
                logging.error(f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}')
                # message_telegram = f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
            
            # insert dba CTS
            try:
                conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                    host=ctshost, port=ctsport, database=ctsdb)
                cur = conn.cursor()
                for chunk4 in chunks4:
                    json_obj4 = json.dumps(chunk4)
                    cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [
                                json_obj4, date_insert, None])
                    conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
        
        return df_result3.to_dict(orient='records')

    except Exception as err:
        logging.error(f'{ENV} | Error in agg function: {err}')
        # message_telegram = f'{ENV} | Error in agg function: {err}'
        # SendLogTelegram.send_message(message_telegram)
        raise ValueError

if __name__ == "__main__":
    check_cus_files=os.listdir(root)
    if cus_list_fn in check_cus_files:
        os.remove(os.path.join(root,cus_list_fn))
    if cus_dict_fn in check_cus_files:
        os.remove(os.path.join(root,cus_dict_fn))
    initial=None
    while True:
        check_files = [f for f in os.listdir(root_orig)]
        if len(check_files) > 0:
            orig_fn = check_files[0]
            if initial is None:
                month_prev=orig_fn.split('.')[0].split('_')[1]
                day_prev=orig_fn.split('.')[0].split('_')[2]
                year_prev=orig_fn.split('.')[0].split('_')[3]
                time_begin = time.time()
                today = dt.today()
                logging.info(
                    "======================================================================================================")
                logging.info(f"{ENV} | Running for Date: {year_prev+'-'+month_prev+'-'+day_prev}")
                message_telegram = f"{ENV} | Group Betting is running for {year_prev+'-'+month_prev+'-'+day_prev}"
                # SendLogTelegram.send_message(message_telegram)
                initial=int(orig_fn.split('.')[0].split('_')[2])
            month_curr=orig_fn.split('.')[0].split('_')[1]
            day_curr=orig_fn.split('.')[0].split('_')[2]
            year_curr=orig_fn.split('.')[0].split('_')[3]
            time_constant=int(day_curr)-int(day_prev)
            if time_constant !=0 :
                date_insert=year_prev+'-'+month_prev+'-'+day_prev
                print(f'{ENV} | date_insert when DAY END {date_insert}')
                with open(os.path.join(root, cus_list_fn), 'rb') as f:
                    CUST_LIST = pickle.load(f)
                with open(os.path.join(root, cus_dict_fn), 'rb') as g:
                    daily_cus_dict = pickle.load(g)
                CUST_LIST = np.sort(CUST_LIST)
                BATCHES = [CUST_LIST[x:x+10] for x in range(0, len(CUST_LIST), 10)]
                pool = mp.Pool(nb_workers_phase_2)
                for _ in tqdm(pool.imap_unordered(day_end_aggregate, [(np.min(BATCH), np.max(BATCH),results,date_insert) for BATCH in BATCHES]), total=len(BATCHES), desc='DAY-END AGG'):
                    pass
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                # update table SystemParameter
                cur.callproc('SPU_AIML.SPU_AIML_UpdateScanStatus',
                            [date_insert, None])
                conn.commit()

                cur.close()
                conn.close()
                print("***********************************************************************************************************************************************************************************")
                print("%s | AGG & INSERT TIME %.0f SECONDS" %
                    (ENV,time.time() - start_time))
                logging.info(
                    f"{ENV} | Done phase 2, takes {time.time() - start_time} seconds")
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
                initial=None
                continue           

            # START PHASE 0 --> PREPARATION
            # *****************************************************************************************************************************************************************************
            # print what time it is now !
            try:
                time_phase0 = time.time()
                t = time.localtime()
                current_time = time.strftime("%H:%M:%S", t)
                print(f"{ENV} | CURRENT TIME : ", current_time)

                # read - filter - preprocess data
                # if ENV=='LOCAL':
                #     data = pd.read_csv(os.path.join(root_orig, orig_fn),encoding='ISO-8859-1')
                # else:
                logging.info(f'Start running file {orig_fn}')
                data = pd.read_csv(os.path.join(root_orig, orig_fn),
                                encoding='ISO-8859-1'
                                , skiprows=[1], skipfooter=1
                                )
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
                print(f"date insert {date_insert}")
                DATE['transdate'] = DATE['transdate'].apply(
                    lambda z: distance_time(separate(date), separate(z)))

                # get list of matches
                matches = DATE.matchid.unique()
                # print(f'Number of matches {len(matches)}')

                # get list of custid
                LS = list(DATE.custid.unique())
                check_cus_files=os.listdir(os.path.join(root))
                # print(f'check_cus_list_file {check_cus_list_file}')
                if cus_list_fn not in check_cus_files:
                    with open(os.path.join(root, cus_list_fn), 'wb') as f:
                        pickle.dump(LS, f)
                else:
                    with open(os.path.join(root, cus_list_fn), 'rb') as f:
                        CUST_LIST = pickle.load(f)
                    LS+=CUST_LIST
                    LS=list(set(LS))
                    with open(os.path.join(root, cus_list_fn), 'wb') as f:
                        pickle.dump(LS, f)

                # match breaking
                check_match_files=os.listdir(os.path.join(root, match_breaking))
                if len(check_match_files)>0:
                    for fn in check_match_files:
                        os.remove(os.path.join(root, match_breaking,fn))
                for n in tqdm(range(len(matches)), desc="MATCH BREAKING"):
                    match = matches[n]
                    m = DATE[DATE.matchid == match]
                    for bt in [1, 3, 7, 8]:
                        f = m[m.bettype == bt]
                        if f.custid.nunique() > 1:
                            f.to_csv(os.path.join(root, match_breaking,
                                                f"{match}_{bt}.csv"), index=False)

                del DATE, data
                print('\n')

                # build cus_dict for count joining combinations
                cus_dict = {}
                ls_mat = os.listdir(os.path.join(root, match_breaking))
                for k in tqdm(range(len(ls_mat)), desc="BUILD CUS DICT"):
                    fn = ls_mat[k]
                    match, bt = int(fn.split('.')[0].split('_')[0]), int(
                        fn.split('.')[0].split('_')[1])
                    df = pd.read_csv(os.path.join(root, match_breaking, fn))

                    ls = df.custid.unique()
                    for cus in ls:
                        if cus not in cus_dict:
                            cus_dict[cus] = [(match, bt)]
                        else:
                            cus_dict[cus].append((match, bt))
                if cus_dict_fn not in check_cus_files:
                    with open(os.path.join(root, cus_dict_fn), 'wb') as g:
                        pickle.dump(cus_dict, g)
                else:
                    with open(os.path.join(root, cus_dict_fn), 'rb') as g:
                        daily_cus_dict = pickle.load(g)
                    for key,value in cus_dict.items():
                        if key not in daily_cus_dict:
                            daily_cus_dict[key]=value
                        else:
                            daily_cus_dict[key]+=value
                    with open(os.path.join(root, cus_dict_fn), 'wb') as g:
                        pickle.dump(daily_cus_dict, g)
                # print('\n', f"LEN OF CUS DICT {len(cus_dict)}")
                with open(os.path.join(root, cus_dict_fn), 'rb') as g:
                        daily_cus_dict = pickle.load(g)
                logging.info(
                    f"{ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
                # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
            except Exception as e:
                logging.error(f"{ENV} | Error at phase 0: {e}")
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
                for _ in tqdm(pool.imap_unordered(process_a_combination, [(candidate,cus_dict) for candidate in candidates]), total=len(candidates), desc='MAIN PROCESS'):
                    pass
                print('\n', '********************************************************************************************************************************************')
                print("\n", f"{ENV} | PROCESSING TIME %.0f SECONDS" %
                    (time.time() - start_processing))
                logging.info(
                    f"{ENV} | Done phase 1, takes {time.time() - start_processing} seconds")
            except Exception as e:
                logging.error(f"{ENV} | Error phase 1: {e}")
                # message_telegram = f"{ENV} | Error phase 1: {e}"
                # SendLogTelegram.send_message(message_telegram)
                break

            # END PHASE 1 - START PHASE 2
            # *****************************************************************************************************************************************************************************
            try:
                start_time = time.time()
                # read customer list
                with open(os.path.join(root, cus_list_fn), 'rb') as f:
                    CUST_LIST = pickle.load(f)

                # build batches
                CUST_LIST = np.sort(CUST_LIST)
                BATCHES = [CUST_LIST[x:x+num_batch_cus] for x in range(0, len(CUST_LIST), num_batch_cus)]

                # aggregate((np.min(BATCHES[0]),np.max(BATCHES[0])))
                # pool = mp.Pool(nb_workers_phase_2)
                # for _ in tqdm(pool.imap_unordered(aggregate, [(np.min(BATCH), np.max(BATCH),0,date_insert,daily_cus_dict) for BATCH in BATCHES]), total=len(BATCHES), desc='AGG'):
                #     pass
                # with ProcessPoolExecutor(max_workers=nb_workers_phase_2) as executor:
                #     canvas=[executor.submit(aggregate,(np.min(BATCH), np.max(BATCH),date_insert,daily_cus_dict)) for BATCH in BATCHES]
                #     results=[]
                #     for f in as_completed(canvas):
                #         results+=f.result()
                pool = mp.Pool(nb_workers_phase_2)
                result = pool.map(aggregate, [(np.min(BATCH), np.max(BATCH),date_insert,daily_cus_dict) for BATCH in BATCHES])
                pool.close()
                results = [item for sublist in result for item in sublist]
                logging.info(f'File {orig_fn} done in {time.time()-start_time} seconds')
                print(f'Once more batch of {date_insert} overcame phase 2 successfully !')

            except Exception as e:
                logging.error(f"{ENV} | Error phase 2: {e}")
                # message_telegram = f"{ENV} | Error phase 2: {e}"
                # SendLogTelegram.send_message(message_telegram)
                break
            
            # remove file when complete
            os.remove(os.path.join(root_orig,orig_fn))
        
        else:
            time.sleep(time_sleep)
    
