import sys
# sys.path.append("/home/vnteam/app/")
# sys.setrecursionlimit(1500)
import pandas as pd
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
import logging
import csv
import re
import json
import warnings
from GroupBetting import helper
from GroupBetting import SendLogTelegram
from GroupBetting import GroupbyIP
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
backup=config.GetBackUp(config)
errorfolder=config.GetErrorFolder(config)

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

def recursiveApp(list_file):
    file_name = list_file.pop(0)
    df = pd.read_csv(os.path.join(root_orig, file_name),
                                encoding='ISO-8859-1'
                                , skiprows=[1], skipfooter=1
                                )
    os.rename(os.path.join(root_orig,file_name),os.path.join(backup,file_name))
    df['file_name'] = file_name
    #print(df.head())
    if len(list_file) == 0:
        return df
    else:
        return pd.concat([df,recursiveApp(list_file)],ignore_index=True)


def process_a_combination(args):
    """
    >>> Input    :  filepath
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
    start_compute = time.time()
    m = helper.compute_pairwise_cus(X, time_threshold)
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
            , "TJC":count_joining_combs_by_batch_cus_dict(COMBINATION_CUST_LIST[i], COMBINATION_CUST_LIST[j],batch_cus_dict)
            , "IML":IMJ
            ,  "IN":1}

        for (i, j) in itertools.combinations([x for x in range(len(COMBINATION_CUST_LIST))], 2) if m[i, j] > 0
    ]
    # print(f"JSON OBJ 1th {obj[0]}",f"JSON OBJ 2nd {obj[1]}",f"JSON OBJ 3rd {obj[2]}",sep='\n')

    start_save = time.time()
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
                in_, out1 = cursor.callproc('SPU_AIML_InsertAssociationStatsStaging', [jsonList, None])
                if out1 is not None:
                    print(out1)
                    logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationStatsStaging: {out1}')
                    message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationStatsStaging: {out1}'
                    SendLogTelegram.send_message(message_telegram)
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            logging.error(f'{ENV} | Error insert AssociationStatsStaging: {err}')
            message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            SendLogTelegram.send_message(message_telegram)
            raise ValueError
    # print("\n", "MATCH %.0f BETTYPE %.0f | %.0f CUSTOMERS | SAVING TAKES %.0f SECONDS" % (
    #     match, bettype, len(COMBINATION_CUST_LIST), time.time() - start_save))
    del chunks, obj
    gc.collect()


def count_joining_combs_by_batch_cus_dict(cus1,cus2,batch_cus_dict):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(batch_cus_dict[cus1]), set(batch_cus_dict[cus2])
    return len(comb_a.intersection(comb_b))

def count_joining_combs_by_daily_cus_dict(cus1,cus2,daily_cus_dict):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(daily_cus_dict[cus1]), set(daily_cus_dict[cus2])
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
    date_insert,daily_cus_dict,the_first_is_the_last=args[2],args[3],args[4]
    try:
        # sub_results=results[(results.C1>=int(args[0]))&(results.C1<=int(args[1]))]
        time_getStaging = time.time()
        conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
        cur = conn.cursor()
        in1,in2,out1 = cur.callproc('SPU_AIML_GetAssociationStats',[int(args[0]), int(args[1]), None])
        if out1 is not None:
            print(out1)
            logging.error(f'{ENV} | Error return from SP SPU_AIML_GetAssociationStats: {out1}')
            message_telegram = f'{ENV} | Error return from SP SPU_AIML_GetAssociationStats: {out1}'
            SendLogTelegram.send_message(message_telegram)
        dba_results = [r.fetchall() for r in cur.stored_results()]
        conn.commit()
        cur.close()
        conn.close()

        if len(dba_results[0]) == 0:
            return True
        df = pd.DataFrame(dba_results[0], columns=[
            "C1"
            ,"C2"
            ,"TS"
            ,"ML"
            ,"BL"
            ,"LeagueID"
            ,"IsMajorLeague"
            ,"TJC"
            ,"IsNew"
            ,"AccTS"
            ,"AccMS"
            ,"AccLS"
            ,"AccTJD"
            ,"AccTJSC"
            ])
        # fill 0 to NaN
        df['AccTS'].fillna(0, inplace=True)
        df['AccMS'].fillna(0, inplace=True)
        df['AccLS'].fillna(0, inplace=True)
        df['AccTJD'].fillna(0, inplace=True)
        df['AccTJSC'].fillna(0, inplace=True)

        df['TJC'] = df.apply(
            lambda z: count_joining_combs_by_daily_cus_dict(z['C1'], z['C2'],daily_cus_dict), axis=1)
        
        df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
        
        df = df.astype({"sample_id": 'int64'})
        df['TS'] = df['TS'].astype('float')
        df['AccTS'] = df['AccTS'].astype('float')
        df['AccMS'] = df['AccMS'].astype('float')
        df['AccLS'] = df['AccLS'].astype('float')

        # df=df[['C1','C2','AccTS','AccMS','AccLS','AccTJD']]
        
        # df=df.drop_duplicates()

        # df_DailyScore=pd.merge(df,sub_results,how='left',left_on=['C1','C2'],right_on=['C1','C2'])
        df_custid = pd.DataFrame()
        df_custid = df.groupby('sample_id')[['C1', 'C2', 'TJC']].first()

        # version 4
        df_parameter = (df.groupby(['sample_id', 'IsMajorLeague', 'LeagueID']).size(
        ).unstack('IsMajorLeague', fill_value=0))
        df_parameter = df_parameter.reset_index()

        df_parameter2 = (df.groupby(['sample_id', 'IsMajorLeague']).size().unstack(
            'IsMajorLeague', fill_value=0))
        df_parameter2 = df_parameter2.reset_index()
        # print(df_parameter2.info())
        #df_parameter2 = df_parameter2.drop(columns=['IsMajor'])
        df_parameter3 = pd.merge(df_parameter, df_parameter2, on=['sample_id'])
        #value_parameter = df_parameter.loc[1,0].to_list()
        if '1_x' not in df_parameter3:
            df_parameter3['1_x'] = 0
            df_parameter3['1_y'] = 0
        if '0_x' not in df_parameter3:
            df_parameter3['0_x'] = 0
            df_parameter3['0_y'] = 0
        # print(df_parameter3.head())
        df_parameter3 = df_parameter3.rename({
            '0_x': 'each_league_0',
            '0_y': 'total_league_0',
            '1_x': 'each_league_1',
            '1_y': 'total_league_1'
        }, axis=1)
        # print(df_parameter3)
        df_parameter3['score_eachleague_0'] = [(x/y)**2 if y != 0 else 0 for x, y in zip(
            df_parameter3['each_league_0'], df_parameter3['total_league_0'])]
        df_parameter3['score_eachleague_1'] = [(x/y)**2 if y != 0 else 0 for x, y in zip(
            df_parameter3['each_league_1'], df_parameter3['total_league_1'])]
        #df_parameter3 = df_parameter2.drop(columns=['total_league_0','total_league_1'])
        # print(df_parameter3.head())
        df_leaguescore = pd.DataFrame()
        df_leaguescore['minor'] = 1 - \
            df_parameter3.groupby('sample_id')['score_eachleague_0'].sum()
        df_leaguescore['major'] = 1 - \
            df_parameter3.groupby('sample_id')['score_eachleague_1'].sum()
        df_leaguescore['LS'] = df_leaguescore.apply(
            lambda x: total_leaguescore(x['minor'], x['major']), axis=1)
        
        #start_time = time.time()
        df_timescore = df.groupby('sample_id')[['TS']].mean()
        #print('----------finish timescore: ', time.time() - start_time)

        # compute MS
        df_matchscore = pd.DataFrame()
        df_matchscore['TJSC'] = df.groupby(['sample_id', 'ML'])[
            'BL'].nunique().groupby('sample_id').sum()
        df_matchscore['MS'] = df_matchscore['TJSC'] / df_custid['TJC']


        # merge all kind of score
        df_result = pd.merge(df_custid, df_timescore,
                             left_index=True, right_index=True)
        df_result2 = pd.merge(df_result, df_matchscore,
                              left_index=True, right_index=True)
        df_result3 = pd.merge(df_result2, df_leaguescore,
                              left_index=True, right_index=True)

        if the_first_is_the_last:
            susinfo = df[['sample_id', 'ML', 'BL']]
            df_susinfo = transform_to_list(susinfo)
            df_susinfo = df_susinfo.set_index('sample_id')
            df_susinfo['ML'] = [','.join(map(str, l)) for l in df_susinfo['ML']]
            df_susinfo['BL'] = [','.join(map(str, l)) for l in df_susinfo['BL']]
            df_resultinfo = pd.merge(df_custid, df_susinfo, left_index=True, right_index=True)
            fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
            chunks2 = [fulldatainfo_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatainfo_dba), chunk_size)]
        
        df_result3 = df_result3.drop(columns=['minor', 'major'])

        # add BC column with default value 1
        df_result3['BC'] = 1
        df_result3['TJD'] = 1
        # aggreagate without history data
        df_result3['S'] = 100 * (df_result3['TS'] + df_result3['MS'] + df_result3['LS']) / 3
    
        df_byAISample03 = df_result3[['C1', 'C2', 'S','TJSC']]
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
        # fulldata_dba = df_result3.to_dict(orient="records")
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
                    in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                    if out1 is not None:
                        print(out1)
                        logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}')
                        message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}'
                        SendLogTelegram.send_message(message_telegram)
                    conn.commit()
                    
            if the_first_is_the_last:
                for chunk2 in chunks2:
                    json_obj2 = json.dumps(chunk2)
                    in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
                    if out1 is not None:
                        print(out1)
                        dataSP_error = json.loads(json_obj2)
                        df_dataSP_error = pd.DataFrame(dataSP_error)
                        df_dataSP_error.to_csv(f"/home/vnteam/Data/ErrorData/file_error_SP_data_{count_sp}.csv",index=False)
                        count_sp += 1
                        logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}')
                        message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}'
                        SendLogTelegram.send_message(message_telegram)
                    conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
            message_telegram = f'{ENV} | Error insert 3 table in DBA when day-end: {err}'
            SendLogTelegram.send_message(message_telegram)
            raise ValueError

        # insert dba CTS
        if transfer_score:
            try:
                conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                    host=ctshost, port=ctsport, database=ctsdb)
                cur = conn.cursor()
                for chunk4 in chunks4:
                    json_obj4 = json.dumps(chunk4)
                    in1,in2,out1 = cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
                    if out1 is not None:
                        print(out1)
                        logging.error(f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}')
                        message_telegram = f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}'
                        SendLogTelegram.send_message(message_telegram)
                    conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                message_telegram = f'{ENV} | Error insert table byAI in DBA CTS when day-end: {err}'
                SendLogTelegram.send_message(message_telegram)
                raise ValueError
        
        # Compute accomulatedly
        df_sampleDailyScore = df[['sample_id', 'C1',
                                  'C2', 'AccTS', 'AccMS', 'AccLS', 'AccTJD', 'AccTJSC']]
        df_DailyScore = df_sampleDailyScore.groupby('sample_id').first()

        #df_result3.set_index('sample_id',inplace=True)
        df_DailyScore = pd.merge(df_DailyScore,df_result3[['TS','MS','LS','TJC','TJSC','BC']],left_index=True, right_index=True)

        df_DailyScore['AccTS'] = df_DailyScore['AccTS'] + df_DailyScore['TS']

        df_DailyScore['AccMS'] = df_DailyScore['AccMS'] + df_DailyScore['MS']

        df_DailyScore['AccLS'] = df_DailyScore['AccLS'] + df_DailyScore['LS']

        df_DailyScore['AccTJSC'] = df_DailyScore['AccTJSC'] + df_DailyScore['TJSC']
    
        df_DailyScore['AccTJD'] += 1
        
        # aggregate with history data
        df_DailyScore['S'] = 100 * (df_DailyScore['AccTS'] + df_DailyScore['AccMS'] +
                                    df_DailyScore['AccLS']) / (3*df_DailyScore['AccTJD'])

        df_DailyScore = df_DailyScore.drop(columns=['TS','MS','LS'])

        df_DailyScore.rename(columns={'AccTS':'TS','AccMS':'MS','AccLS':'LS','AccTJD':'TJD'},inplace=True)

        
        df_byAISample03 = df_DailyScore[['C1', 'C2', 'S','AccTJSC']]
        df_byAISample03.rename(columns={'AccTJSC':'TJSC'},inplace=True)
        df_byAI = df_byAISample03[(df_byAISample03['S'] >= percent_score) & (
            df_byAISample03['TJSC'] >= combination_threshold)]
                
        isTraceLog = False
        df_byAISPU = pd.DataFrame()
        if len(df_byAI.index) != 0:
            isTraceLog = True
            df_result4 = df_DailyScore[['TS', 'MS', 'LS', 'TJD', 'TJC']]
            df_byAISPU = pd.merge(df_result4, df_byAI,
                                left_index=True, right_index=True)

        # move to dba
        fulldata_dba = df_DailyScore.to_dict(orient="records")
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
                for chunk5 in chunks5:
                    json_obj5 = json.dumps(chunk5)
                    in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                    if out1 is not None:
                        print(out1)
                        logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}')
                        message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}'
                        SendLogTelegram.send_message(message_telegram)
                    conn.commit()
                    
            for chunk1 in chunks1:
                json_obj1 = json.dumps(chunk1)
                in1,in2,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationStats', [json_obj1, date_insert, None])
                if out1 is not None:
                    print(out1)
                    logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationStats: {out1}')
                    message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationStats: {out1}'
                    SendLogTelegram.send_message(message_telegram)
                conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
            message_telegram = f'{ENV} | Error insert 3 table in DBA when Acc day-end: {err}'
            SendLogTelegram.send_message(message_telegram)
            raise ValueError

        # insert dba CTS
        if transfer_score:
            try:
                conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                    host=ctshost, port=ctsport, database=ctsdb)
                cur = conn.cursor()
                for chunk4 in chunks4:
                    json_obj4 = json.dumps(chunk4)
                    in1,in2,out1 = cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
                    if out1 is not None:
                        print(out1)
                        logging.error(f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}')
                        message_telegram = f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}'
                        SendLogTelegram.send_message(message_telegram)
                    conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                logging.error(f'{ENV} | Error insert table byAI in DBA CTS when Acc day-end: {err}')
                message_telegram = f'{ENV} | Error insert table byAI in DBA CTS when Acc day-end: {err}'
                SendLogTelegram.send_message(message_telegram)
                raise ValueError
        logging.info(f"Time to complete child process into phase Acc day-end {os.getpid()}: {time.time() - time_getStaging}")
    except Exception as err:
        logging.error(f'{ENV} | Error in day-end agg function: {err}')
        message_telegram = f'{ENV} | Error in day-end agg function: {err}'
        SendLogTelegram.send_message(message_telegram)
        raise ValueError

def aggregate(args):
    date_insert,daily_cus_dict=args[1],args[2]
    try:
        time_getStaging = time.time()
        conn = MySQLConnection(user=aimluser, password=aimlpwd,
                            host=aimlhost, port=aimlport, database=aimldb)
        cur = conn.cursor()
        in1,out1 = cur.callproc('SPU_AIML_GetAssociationStatsStaging',[args[0], None])
        if out1 is not None:
            print(out1)
            logging.error(f'{ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1}')
            message_telegram = f'{ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1}'
            SendLogTelegram.send_message(message_telegram)
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
        #logging.info(f"Time get data from StatStaging: {time.time() - time_getStaging}")
        if len(IsNewdf)>0:
            time_newBatch = time.time()
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
            # df_result3['BC'] = 1
            df_resultinfo = df_resultinfo.drop(columns=['TJC'])
            df_result3['S'] = 100 * (df_result3['TS'] + df_result3['MS'] + df_result3['LS']) / 3
            df_byAISample03 = df_result3[['C1', 'C2', 'S','TJSC']]
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
            #logging.info(f"Time to calculate new batch: {time.time() - time_newBatch}")
            time_inserttable = time.time()
            try:
                
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                if isTraceLog:
                    for (chunk2, chunk5) in zip(chunks2, chunks5):

                        json_obj2 = json.dumps(chunk2)
                        in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
                        if out1 is not None:
                            print(out1)
                            dataSP_error = json.loads(json_obj2)
                            df_dataSP_error = pd.DataFrame(dataSP_error)
                            df_dataSP_error.to_csv(errorfolder+f"file_error_SP_data_{count_sp}.csv",index=False)
                            count_sp += 1
                            logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}')
                            message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}'
                            SendLogTelegram.send_message(message_telegram)
                        conn.commit()
                        
                        json_obj5 = json.dumps(chunk5)
                        in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                        if out1 is not None:
                            print(out1)
                            logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}')
                            message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}'
                            SendLogTelegram.send_message(message_telegram)
                        conn.commit()
                else:
                    for chunk2 in chunks2:
                        json_obj2 = json.dumps(chunk2)
                        in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
                        if out1 is not None:
                            print(out1)
                            dataSP_error = json.loads(json_obj2)
                            df_dataSP_error = pd.DataFrame(dataSP_error)
                            df_dataSP_error.to_csv(errorfolder+f"file_error_SP_data_{count_sp}.csv",index=False)
                            count_sp += 1
                            logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}')
                            message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}'
                            SendLogTelegram.send_message(message_telegram)
                        conn.commit()
                cur.close()
                conn.close()
            except Exception as err:
                logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
                message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
                SendLogTelegram.send_message(message_telegram)
                raise ValueError
            
            # insert dba CTS
            if transfer_score:
                try:
                    conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                        host=ctshost, port=ctsport, database=ctsdb)
                    cur = conn.cursor()
                    for chunk4 in chunks4:
                        json_obj4 = json.dumps(chunk4)
                        in1,in2,out1 = cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
                        if out1 is not None:
                            print(out1)
                            logging.error(f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}')
                            message_telegram = f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}'
                            SendLogTelegram.send_message(message_telegram)
                        conn.commit()

                    cur.close()
                    conn.close()

                except Exception as err:
                    logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                    message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                    SendLogTelegram.send_message(message_telegram)
                    raise ValueError
            
            # update Staging Status
            try:
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                #cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [
                            #int(args[0]), int(args[1]), None])
                in1,out1 = cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [args[0], None])
                if out1 is not None:
                    print(out1)
                    logging.error(f'{ENV} | Error return from SP SPU_AIML_UpdateAssociationStatsStagingStatus: {out1}')
                    message_telegram = f'{ENV} | Error return from SP SPU_AIML_UpdateAssociationStatsStagingStatus: {out1}'
                    SendLogTelegram.send_message(message_telegram)
                conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                logging.error(f'{ENV} | Error Update Staging Status: {err}')
                message_telegram = f'{ENV} | Error Update Staging Status: {err}'
                SendLogTelegram.send_message(message_telegram)
                raise ValueError
            #logging.info(f"Time to insert all table in DB: {time.time() - time_inserttable}")
        if len(df)>len(IsNewdf):
            time_onthefly = time.time()
            df['TJC']=df.apply(lambda z : count_joining_combs_by_daily_cus_dict(z['C1'],z['C2'],daily_cus_dict),axis=1)
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
            df_result3['S'] = 100 * (df_result3['TS'] + df_result3['MS'] + df_result3['LS']) / 3
            df_byAISample03 = df_result3[['C1', 'C2', 'S','TJSC']]
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
            #logging.info(f"Time to calculate onthefly: {time.time() - time_onthefly}")
            time_inserttable = time.time()
            try:
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                if isTraceLog:
                    for chunk5 in chunks5:                     
                        json_obj5 = json.dumps(chunk5)
                        in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                        if out1 is not None:
                            print(out1)
                            logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}')
                            message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}'
                            SendLogTelegram.send_message(message_telegram)
                        conn.commit()
                cur.close()
                conn.close()
            except Exception as err:
                logging.error(f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}')
                message_telegram = f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}'
                SendLogTelegram.send_message(message_telegram)
                raise ValueError
            
            # insert dba CTS
            if transfer_score:
                try:
                    conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                        host=ctshost, port=ctsport, database=ctsdb)
                    cur = conn.cursor()
                    for chunk4 in chunks4:
                        json_obj4 = json.dumps(chunk4)
                        in1,in2,out1 = cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
                        if out1 is not None:
                            print(out1)
                            logging.error(f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}')
                            message_telegram = f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}'
                            SendLogTelegram.send_message(message_telegram)
                        conn.commit()

                    cur.close()
                    conn.close()

                except Exception as err:
                    logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                    message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                    SendLogTelegram.send_message(message_telegram)
                    raise ValueError
        logging.info(f"Time to complete child process {os.getpid()}: {time.time() - time_getStaging}")
        

    except Exception as err:
        logging.error(f'{ENV} | Error in agg function: {err}')
        message_telegram = f'{ENV} | Error in agg function: {err}'
        SendLogTelegram.send_message(message_telegram)
        raise ValueError

if __name__ == "__main__":
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
    count = 1
    count_sp = 1
    # results=None
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
                today = dt.today()
                logging.info(
                    "======================================================================================================")
                logging.info(f"{ENV} | Running for Date: {year_prev+'-'+month_prev+'-'+day_prev}")
                message_telegram = f"{ENV} | Group Betting is running for {year_prev+'-'+month_prev+'-'+day_prev}"
                SendLogTelegram.send_message(message_telegram)
                initial.append(day_prev)
            

            # START PHASE 0 --> PREPARATION
            # *****************************************************************************************************************************************************************************
            # print what time it is now !
            # try:
            #     del results
            # except:
            #     print('results variable is not defined')
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
                # data = pd.read_csv(os.path.join(root_orig, orig_fn),
                #                 encoding='ISO-8859-1'
                #                 , skiprows=[1], skipfooter=1
                #                 )
                logging.info(f"Total file: {len(check_files_sameday)}")
                ### use recursive to concat data
                #data = recursiveApp(check_files_sameday)
                
                ### use list comprehensive to concat data
                data = pd.concat((pd.read_csv(os.path.join(root_orig, f),encoding='ISO-8859-1', skiprows=[1], skipfooter=1).assign(file_name = f) for f in check_files_sameday))
                for file in check_files_sameday:
                    os.rename(os.path.join(root_orig,file),os.path.join(backup,file))
                logging.info(f"Number of rows: {len(data)}")
                if len(data.index)==0:
                    for file in check_files_sameday:
                        os.remove(os.path.join(root_orig, file))
                    # logging.error(f'File Error {orig_fn}')
                    # print(f'File Error {orig_fn}')
                    continue
                if data.bettype.isnull().values.any():
                    # os.remove(os.path.join(root_orig, orig_fn))
                    logging.error(f'File Error {orig_fn} | Bettype Column Null')
                    print(f'File Error {orig_fn} | Bettype Column Null')
                    for file in check_files_sameday:
                        os.rename(os.path.join(root_orig, file),os.path.join(root,'NullBettype',file))
                    continue
                #data.to_csv("/home/vnteam/backupdata.csv",index=False)
                ### clean missing data
                data.dropna(subset=['custid', 'matchid', 'transdate', 'bettype','leagueid'],inplace=True)
                df_nan = data[data[['custid', 'matchid', 'transdate', 'bettype','leagueid']].isna().any(axis=1)]
                
                if len(df_nan.index) == 0:
                    data.to_csv(errorfolder+f"file_error_data_{count}.csv",index=False)
                    count +=1
                DATE = data[(data.bettype.isin([1, 3, 7, 8]))
                            & (data.liveindicator)]
                df_dataip = data[(data.bettype.isin([1, 3, 7, 8]))
                        & (data.liveindicator)]
                if len(DATE.index)==0:
                    logging.error(f'File Error {orig_fn} | No Live')
                    print(f'File Error {orig_fn} | No Live')
                    os.rename(os.path.join(root_orig, orig_fn),os.path.join(root,'NoLive',orig_fn))
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
                    lambda z: distance_time(separate(date), separate(z)))

                # get list of matches
                matches = DATE.matchid.unique()
                # print(f'Number of matches {len(matches)}')

                # get list of custid
                batch_cus_list = list(DATE.custid.unique())
                check_cus_files=os.listdir(os.path.join(root))
                # print(f'check_cus_list_file {check_cus_list_file}')
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
                batch_cus_dict = {}
                ls_mat = os.listdir(os.path.join(root, match_breaking))
                for k in tqdm(range(len(ls_mat)), desc="BUILD CUS DICT"):
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
                # print('\n', f"LEN OF CUS DICT {len(cus_dict)}")
                with open(os.path.join(root, cus_dict_fn), 'rb') as g:
                        daily_cus_dict = pickle.load(g)
                logging.info(
                    f"{ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
                # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
            except Exception as e:
                logging.error(f"{ENV} | Error at phase 0: {e}")
                message_telegram = f"{ENV} | Error at phase 0: {e}"
                SendLogTelegram.send_message(message_telegram)
                break

            # START PHASE ASSOCIATION BY IP 
            # *****************************************************************************************************************************************************************************
            try:
                logging.info(f"{ENV} |Group Betting by IP is running")
                # message_telegram = f"{ENV} |Group Betting by IP is running"
                # SendLogTelegram.send_message(message_telegram)
                df_dataip = df_dataip[['custid','ip','bettype','matchid','leagueid','homeid','awayid','transdate']]
                GroupbyIP.AssociationbyIP(df_dataip,chunk_size,date_insert,transfer_ip)
                del df_dataip
            except Exception as e:
                logging.error(f"{ENV} | Error at phase Association by IP: {e}")
                message_telegram = f"{ENV} | Error at phase Association by IP: {e}"
                SendLogTelegram.send_message(message_telegram)
                break
            # END PHASE 0 - START PHASE 1
            # ****************************************************************************************************************************************************************************
            try:
                start_processing = time.time()

                candidates = os.listdir(os.path.join(root, match_breaking))
                pool = mp.Pool(nb_workers_phase_1)
                # pool.map(process_a_combination,candidates)
                # process_a_combination('39960404_3.csv')
                for _ in tqdm(pool.imap_unordered(process_a_combination, [(candidate,batch_cus_dict) for candidate in candidates]), total=len(candidates), desc='MAIN PROCESS'):
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
                logging.error(f"{ENV} | Error phase 1: {e}")
                message_telegram = f"{ENV} | Error phase 1: {e}"
                SendLogTelegram.send_message(message_telegram)
                break

            # END PHASE 1 - START PHASE 2
            # *****************************************************************************************************************************************************************************
            check_files = [f for f in sorted(os.listdir(root_orig))]
            while len(check_files)==0:
                time.sleep(time_sleep)
                check_files = [f for f in sorted(os.listdir(root_orig))]
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
                        BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+num_batch_cus]]) for x in range(0, len(batch_cus_list), num_batch_cus)]
                        # print('First Batch',BATCHES[0],sep='\n')
                        # logging.info(f"number of cust list: {len(batch_cus_list)}")
                        logging.info(f"number of cust list: {len(batch_cus_list)}")
                        pool = mp.Pool(nb_workers_phase_2)
                        # result = pool.map(aggregate, [(np.min(BATCH), np.max(BATCH),date_insert,daily_cus_dict) for BATCH in BATCHES])
                        for _ in tqdm(pool.imap_unordered(aggregate,BATCHES),total=len(BATCHES),desc=f'AGG | A BATCH OF {date_insert}'):
                            pass
                        pool.close()
                        pool.join()
                        logging.info(f'A BATCH of {date_insert} done in {time.time()-start_time} seconds')
                        # print(f'Once more batch of {date_insert} overcame phase 2 successfully !')

                    except Exception as e:
                        logging.error(f"{ENV} | Error phase 2 right before day end: {e}")
                        # print(f"{ENV} | Error phase 2: {e}")
                        message_telegram = f"{ENV} | Error phase 2 right before day end: {e}"
                        SendLogTelegram.send_message(message_telegram)
                        break
                else:
                    the_first_is_the_last = True
                date_insert=year_prev+'-'+month_prev+'-'+day_prev
                print(f'{ENV} | date_insert when DAY END {date_insert}')
                with open(os.path.join(root, cus_list_fn), 'rb') as f:
                    daily_cus_list = pickle.load(f)
                with open(os.path.join(root, cus_dict_fn), 'rb') as g:
                    daily_cus_dict = pickle.load(g)
                daily_cus_list = np.sort(daily_cus_list)
                BATCHES = [daily_cus_list[x:x+num_batch_cus] for x in range(0, len(daily_cus_list), num_batch_cus)]
                #BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+num_batch_cus]]) for x in range(0, len(batch_cus_list), num_batch_cus)]
                pool = mp.Pool(nb_workers_phase_2)
                for _ in tqdm(pool.imap_unordered(day_end_aggregate,[(min(BATCH),max(BATCH),date_insert,daily_cus_dict,the_first_is_the_last) for BATCH in BATCHES]), total=len(BATCHES), desc='DAY-END AGG'):
                    pass
                pool.close()
                pool.join()
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                # update table SystemParameter
                in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_UpdateScanStatus',[date_insert, None])
                if out1 is not None:
                    print(out1)
                    logging.error(f'{ENV} | Error return from SP SPU_AIML_UpdateScanStatus: {out1}')
                    message_telegram = f'{ENV} | Error return from SP SPU_AIML_UpdateScanStatus: {out1}'
                    SendLogTelegram.send_message(message_telegram)
                conn.commit()

                cur.close()
                conn.close()
                print("***********************************************************************************************************************************************************************************")
                print("%s | AGG & INSERT TIME %.0f SECONDS" %
                    (ENV,time.time() - start_time))
                logging.info(
                    f"{ENV} | Done phase 2 at the end of the day, takes {time.time() - start_time} seconds")
                message_telegram = f"{ENV} | Group Betting is done, total {round((time.time() - time_begin)/3600,4)} hours "
                SendLogTelegram.send_message(message_telegram)
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
            try:
                start_time = time.time()
                # read customer list
                # with open(os.path.join(root, cus_list_fn), 'rb') as f:
                #     daily_cus_list = pickle.load(f)

                # build batches
                batch_cus_list = sorted(batch_cus_list)
                #BATCHES = [daily_cus_list[x:x+num_batch_cus] for x in range(0, len(daily_cus_list), num_batch_cus)]
                BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+num_batch_cus]]) for x in range(0, len(batch_cus_list), num_batch_cus)]
                logging.info("*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*")
                logging.info(f"number of cust list: {len(batch_cus_list)}")
                pool = mp.Pool(nb_workers_phase_2)
                # for _ in tqdm(pool.imap_unordered(aggregate, [(np.min(BATCH), np.max(BATCH)) for BATCH in BATCHES]), total=len(BATCHES), desc='AGG'):
                #     pass
                # pandarallel.initialize(nb_workers=nb_workers_phase_2)
                # MYSERIE = pd.Series(BATCHES)
                # MYSERIE.parallel_apply(lambda z : aggregate((min(z),max(z))))
                #*********************************************************
                # with ProcessPoolExecutor(max_workers=nb_workers_phase_2) as executor:
                #     canvas=[executor.submit(aggregate,(np.min(BATCH), np.max(BATCH),date_insert,daily_cus_dict)) for BATCH in BATCHES]
                #     results=[]
                #     for f in as_completed(canvas):
                #         results+=f.result()
                # pool = mp.Pool(nb_workers_phase_2,maxtasksperchild=1000)
                # bigls = pool.map(aggregate, [(np.min(BATCH), np.max(BATCH)) for BATCH in BATCHES])
                #*********************************************************
                for _ in tqdm(pool.imap_unordered(aggregate,[(BATCH,date_insert,daily_cus_dict) for BATCH in BATCHES]), total=len(BATCHES), desc='AGG'):
                    pass
                pool.close()
                pool.join()
                # myls = [item for sublist in bigls for item in sublist]
                # results = pd.DataFrame(myls)
                logging.info(f'{ENV} | Done phase 2, takes {time.time()-start_time} seconds')
                # print(f'Once more batch of {date_insert} overcame phase 2 successfully !')

            except Exception as e:
                logging.error(f"{ENV} | Error phase 2: {e}")
                message_telegram = f"{ENV} | Error phase 2: {e}"
                SendLogTelegram.send_message(message_telegram)
                break
            
            # remove file when complete
            # os.remove(os.path.join(root_orig,orig_fn))
            #os.rename(os.path.join(root_orig,orig_fn),os.path.join(backup,orig_fn))
            # print("-.-.-.-.-.-.-.--.-.-.-.-.-.-.--.-.-.-.-.-.-.--.-.-.-.-.-.-.-")
            # local_vars = list(locals().items())
            # for var, obj in local_vars:
            #     logging.info('%s occupied %.0f bytes' % (var, sys.getsizeof(obj)))
        
        else:
            time.sleep(time_sleep)
    
