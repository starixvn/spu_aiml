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
    # root = "/home/vnteam/Data/MatchData/"
    root=config.GetSaveDataDir(config)
    # root_orig = "/home/vndata4ai/"
    root_orig=config.GetPathCsvFile(config)
    # orig_fn="bettrans_01_31_2021.csv"
    orig_fn=config.GetNameFile(config)
    match_breaking=config.GetMatchBreaking(config)
    # cus_list_fn = 'cus_list.pkl'
    cus_list_fn=config.GetListName(config)
    # cus_dict_fn = 'cus_dict.pkl'
    cus_dict_fn=config.GetDictName(config)
    # mlm_dict_fn = 'match_league_map.pkl'
    mlm_dict_fn=config.GetMatchLeagueMap(config)


    # define chunk_size for DB saving
    chunk_size = int(config.getChunkSize(config))

    # define nb_workers_phase_1
    nb_workers_phase_1 = int(config.getNumberWorkerPhase1(config))

    # define nb_workers_phase_2
    nb_workers_phase_2 = int(config.getNumberWorkerPhase2(config))

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
    # root = "/home/vnteam/Data/MatchData/"
    root=config.GetSaveDataDir(config)
    # root_orig = "/home/vndata4ai/"
    root_orig=config.GetPathCsvFile(config)
    # orig_fn="bettrans_01_31_2021.csv"
    orig_fn=config.GetNameFile(config)
    match_breaking=config.GetMatchBreaking(config)
    # cus_list_fn = 'cus_list.pkl'
    cus_list_fn=config.GetListName(config)
    # cus_dict_fn = 'cus_dict.pkl'
    cus_dict_fn=config.GetDictName(config)
    # mlm_dict_fn = 'match_league_map.pkl'
    mlm_dict_fn=config.GetMatchLeagueMap(config)


    # define chunk_size for DB saving
    chunk_size = int(config.getChunkSize(config))

    # define nb_workers_phase_1
    nb_workers_phase_1 = int(config.getNumberWorkerPhase1(config))

    # define nb_workers_phase_2
    nb_workers_phase_2 = int(config.getNumberWorkerPhase2(config))

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

def transform_to_list(df):
    keys, values1, values2 = df.sort_values('sample_id').values.T
    ukeys, index = np.unique(keys, True)
    arrays = np.split(values1, index[1:])
    arrays2 = np.split(values2, index[1:])
    df2 = pd.DataFrame({'sample_id': ukeys, 'ML': [list(
        a) for a in arrays], 'BL': [list(b) for b in arrays2]})
    # print(df2)
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

def count_joining_combs(cus1, cus2,cus_dict):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(cus_dict[cus1]), set(cus_dict[cus2])
    return len(comb_a.intersection(comb_b))

def aggregate(args):
        date_insert,daily_cus_dict=args[2],args[3]
    # try:
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
        # TJC=np.sum(df['TJC'].unique())
        # df['TJC'] = TJC
        IsNewdf=df[df.IsNew==1]
        if len(IsNewdf)>0:
            IsNewdf['sample_id'] = IsNewdf['C1'].map(str) + IsNewdf['C2'].map(str)
            IsNewdf = IsNewdf.astype({"sample_id": 'int64'})
            IsNewdf['TS'] = IsNewdf['TS'].astype('float')
            df_custid = pd.DataFrame()
            df_custid = IsNewdf.groupby('sample_id')[['C1', 'C2', 'TJC']].first()
            # df_leaguescore = pd.DataFrame()
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
            df_sampleDailyScore = IsNewdf[['sample_id', 'C1',
                                            'C2'
                                            #   ,'AccTS', 'AccMS', 'AccLS', 'AccTJD'
                                    ]]
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

            # fulldata_dba = df_result3.to_dict(orient="records")
            # print(f'fulldata_dba {fulldata_dba}')
            fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
            # fulldataDailyScore_dba = df_DailyScore.to_dict(orient="records")
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")
            # fulldataNoneAISPU_dba = df_NoneAI.to_dict(orient="records")

            # chunks1 = [fulldata_dba[x:x+chunk_size]
            #         for x in range(0, len(fulldata_dba), chunk_size)]

            chunks2 = [fulldatainfo_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatainfo_dba), chunk_size)]

            # chunks3 = [fulldataDailyScore_dba[x:x+chunk_size]
            #            for x in range(0, len(fulldataDailyScore_dba), chunk_size)]

            chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]
            
            # try:
            #     conn = MySQLConnection(user=aimluser, password=aimlpwd,
            #                         host=aimlhost, port=aimlport, database=aimldb)
            #     cur = conn.cursor()
            #     if isTraceLog:
            #         for (chunk2, chunk5) in zip(chunks2, chunks5):

            #             json_obj2 = json.dumps(chunk2)
            #             cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
            #                         json_obj2, None])
            #             conn.commit()


                        
            #             json_obj5 = json.dumps(chunk5)
            #             cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [
            #                             json_obj5, None])
            #             conn.commit()
            #     else:
            #         for chunk2 in chunks2:

            #             json_obj2 = json.dumps(chunk2)
            #             cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
            #                         json_obj2, None])
            #             conn.commit()
            #     cur.close()
            #     conn.close()
            # except Exception as err:
            #     logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
            #     message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
            #     SendLogTelegram.send_message(message_telegram)
            #     raise ValueError
            
            # insert dba CTS
            # try:
            #     conn = MySQLConnection(user=ctsuser, password=ctspwd,
            #                         host=ctshost, port=ctsport, database=ctsdb)
            #     cur = conn.cursor()
            #     for chunk4 in chunks4:
            #         json_obj4 = json.dumps(chunk4)
            #         cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [
            #                     json_obj4, date_insert, None])
            #         conn.commit()

            #     cur.close()
            #     conn.close()

            # except Exception as err:
            #     logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
            #     message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            #     SendLogTelegram.send_message(message_telegram)
            #     raise ValueError
            
            # update Staging Status
            # try:
            #     conn = MySQLConnection(user=aimluser, password=aimlpwd,
            #                         host=aimlhost, port=aimlport, database=aimldb)
            #     cur = conn.cursor()
            #     cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [
            #                 int(args[0]), int(args[1]), None])
            #     conn.commit()

            #     cur.close()
            #     conn.close()

            # except Exception as err:
            #     logging.error(f'{ENV} | Error Update Staging Status: {err}')
            #     message_telegram = f'{ENV} | Error Update Staging Status: {err}'
            #     SendLogTelegram.send_message(message_telegram)
            #     raise ValueError
        # IsNewdf=df[df.IsNew==1]
        if len(df)>len(IsNewdf):
            # uni=df.groupby(['C1','C2'])['TJC'].unique().reset_index()
            df['TJC']=df.apply(lambda z : count_joining_combs(z['C1'],z['C2'],daily_cus_dict),axis=1)
            # df=pd.merge(df.loc[:,df.columns != 'TJC'],uni,how='left',left_on=['C1','C2'],right_on=['C1','C2'])
            df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
            df = df.astype({"sample_id": 'int64'})
            df['TS'] = df['TS'].astype('float')
            df_custid = pd.DataFrame()
            df_custid = df.groupby('sample_id')[['C1', 'C2', 'TJC']].first()
            # df_leaguescore = pd.DataFrame()
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
            # print(df_result2.head())
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
            df_sampleDailyScore = df[['sample_id', 'C1',
                                            'C2'
                                            #   ,'AccTS', 'AccMS', 'AccLS', 'AccTJD'
                                    ]]
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

            # fulldata_dba = df_result3.to_dict(orient="records")
            # print(f'fulldata_dba {fulldata_dba}')
            # fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
            # fulldataDailyScore_dba = df_DailyScore.to_dict(orient="records")
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")
            # fulldataNoneAISPU_dba = df_NoneAI.to_dict(orient="records")

            # chunks1 = [fulldata_dba[x:x+chunk_size]
            #         for x in range(0, len(fulldata_dba), chunk_size)]

            # chunks2 = [fulldatainfo_dba[x:x+chunk_size]
            #         for x in range(0, len(fulldatainfo_dba), chunk_size)]

            # chunks3 = [fulldataDailyScore_dba[x:x+chunk_size]
            #            for x in range(0, len(fulldataDailyScore_dba), chunk_size)]

            chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]
        
            # try:
            #     conn = MySQLConnection(user=aimluser, password=aimlpwd,
            #                         host=aimlhost, port=aimlport, database=aimldb)
            #     cur = conn.cursor()
            #     if isTraceLog:
            #         for chunk5 in chunks5:

                        
            #             json_obj5 = json.dumps(chunk5)
            #             cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [
            #                             json_obj5, None])
            #             conn.commit()
            #     cur.close()
            #     conn.close()
            # except Exception as err:
            #     logging.error(f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}')
            #     message_telegram = f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}'
            #     SendLogTelegram.send_message(message_telegram)
            #     raise ValueError
            
            # insert dba CTS
            # try:
            #     conn = MySQLConnection(user=ctsuser, password=ctspwd,
            #                         host=ctshost, port=ctsport, database=ctsdb)
            #     cur = conn.cursor()
            #     for chunk4 in chunks4:
            #         json_obj4 = json.dumps(chunk4)
            #         cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [
            #                     json_obj4, date_insert, None])
            #         conn.commit()

            #     cur.close()
            #     conn.close()

            # except Exception as err:
            #     logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
            #     message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
            #     SendLogTelegram.send_message(message_telegram)
            #     raise ValueError
        
        return df_result3.to_dict(orient='records')

    # except Exception as err:
    #     logging.error(f'{ENV} | Error in agg function: {err}')
    #     message_telegram = f'{ENV} | Error in agg function: {err}'
    #     SendLogTelegram.send_message(message_telegram)
    #     raise ValueError

def day_end_aggregate(args):
    results=pd.DataFrame(args[2])
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
    #print("vo duoc dba")
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
        #time_readfile = time.time()
        # fill none to 0
    df['AccTS'].fillna(0, inplace=True)
    df['AccMS'].fillna(0, inplace=True)
    df['AccLS'].fillna(0, inplace=True)
    df['AccTJD'].fillna(0, inplace=True)

       
    # df['TJC']=df.apply(lambda z : count_joining_combs(z['C1'],z['C2'],daily_cus_dict),axis=1)
    # df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)

    # df = df.astype({"sample_id": 'int64'})
    df['TS'] = df['TS'].astype('float')
    df['AccTS'] = df['AccTS'].astype('float')
    df['AccMS'] = df['AccMS'].astype('float')
    df['AccLS'] = df['AccLS'].astype('float')

    df=df[['C1','C2','AccTS','AccMS','AccLS','AccTJD']]
    
    df=df.drop_duplicates()

    df_DailyScore=pd.merge(df,sub_results,how='left',left_on=['C1','C2'],right_on=['C1','C2'])

    #*********************************************************************
    df_DailyScore['AccTS'] = df_DailyScore['AccTS'] + df_DailyScore['TS']
    # df_DailyScore['TS'] = df_result3['TS']
    df_DailyScore['AccMS'] = df_DailyScore['AccMS'] + df_DailyScore['MS']
    # df_DailyScore['MS'] = df_result3['MS']
    df_DailyScore['AccLS'] = df_DailyScore['AccLS'] + df_DailyScore['LS']
    # df_DailyScore['LS'] = df_result3['LS']
    df_DailyScore['AccTJD'] += 1

    # df_result3['TS'] = df_DailyScore['AccTS']
    # df_result3['MS'] = df_DailyScore['AccMS']
    # df_result3['LS'] = df_DailyScore['AccLS']
    # df_result3['TJD'] = df_DailyScore['AccTJD']
    #*********************************************************************

        # df_DailyScore['S'] = 100 * (df_DailyScore['AccTS'] + df_DailyScore['AccMS'] *
        #                             df_DailyScore['AccLS']) / (df_DailyScore['AccTJD']*(df_DailyScore['AccTJD'] + 1))

    df_DailyScore['S'] = 100 * (df_DailyScore['AccTS'] + df_DailyScore['AccMS'] +
                                df_DailyScore['AccLS']) / 3

    # df_DailyScore = df_DailyScore.drop(
    #     columns=['AccTS', 'AccMS', 'AccLS', 'AccTJD'])

    df_byAISample01 = df_DailyScore['TJSC']
    df_byAISample02 = df_DailyScore[['C1', 'C2', 'S']]
    df_byAISample03 = pd.merge(
        df_byAISample02, df_byAISample01, left_index=True, right_index=True)
    df_byAI = df_byAISample03[(df_byAISample03['S'] >= percent_score) & (
        df_byAISample03['TJSC'] >= combination_threshold)]
            
            # df_NoneAI = df_byAISample03[(df_byAISample03['S'] < percent_score) | (
            #     df_byAISample03['TJSC'] < combination_threshold)]

        # prepare data to table byAI in SPU_AIML to log time couple come to byAI CTS
        # {"C1": 43693, "C2": 45, "TS": 1, "MS": 1, "LS": 0.8, "S": 70, "TJD": 1, "TJC": 3, "TJSC": 2}
    isTraceLog = False
    df_byAISPU = pd.DataFrame()
    if len(df_byAI.index) != 0:
        isTraceLog = True
        df_result4 = df_DailyScore[['TS', 'MS', 'LS', 'TJD', 'TJC']]
        df_byAISPU = pd.merge(df_result4, df_byAI,
                            left_index=True, right_index=True)

    # move to dba

    fulldata_dba = df_DailyScore.to_dict(orient="records")
    # fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
    # fulldataDailyScore_dba = df_DailyScore.to_dict(orient="records")
    fulldatabyAI_dba = df_byAI.to_dict(orient="records")
    fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")
    # fulldataNoneAISPU_dba = df_NoneAI.to_dict(orient="records")

    chunks1 = [fulldata_dba[x:x+chunk_size]
            for x in range(0, len(fulldata_dba), chunk_size)]

    # chunks2 = [fulldatainfo_dba[x:x+chunk_size]
    #         for x in range(0, len(fulldatainfo_dba), chunk_size)]

    # chunks3 = [fulldataDailyScore_dba[x:x+chunk_size]
    #            for x in range(0, len(fulldataDailyScore_dba), chunk_size)]

    chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
            for x in range(0, len(fulldatabyAI_dba), chunk_size)]

    chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
            for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]
    
    # chunks6 = [fulldataNoneAISPU_dba[x:x+chunk_size]
    #         for x in range(0, len(fulldataNoneAISPU_dba), chunk_size)]

    try:
        conn = MySQLConnection(user=aimluser, password=aimlpwd,
                            host=aimlhost, port=aimlport, database=aimldb)
        cur = conn.cursor()
        # for (chunk1, chunk2, chunk3, chunk5) in zip(chunks1, chunks2, chunks3, chunks5):
        if isTraceLog:
            for (chunk1, chunk5) in zip(chunks1, chunks5):
            # for (chunk2, chunk5) in zip(chunks2, chunks5):
                json_obj1 = json.dumps(chunk1)
                cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationStats', [
                            json_obj1, date_insert, None])
                conn.commit()

                # json_obj2 = json.dumps(chunk2)
                # cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
                #             json_obj2, None])
                # conn.commit()

                # json_obj3 = json.dumps(chunk3)
                # cur.callproc('SPU_AIML.SPU_AIML_InsertDailyScore',
                #              [json_obj3, None])
                # conn.commit()

                
                json_obj5 = json.dumps(chunk5)
                cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [
                                json_obj5, None])
                conn.commit()
                # else:
                # json_obj6 = json.dumps(chunk6)
                # cur.callproc('SPU_AIML.SPU_AIML_InsertCoupleDailyStats', [
                #                 json_obj6, None])
                # conn.commit()
        else:
            # for (chunk1, chunk2) in zip(chunks1, chunks2):
            for chunk1 in chunks1:
                json_obj1 = json.dumps(chunk1)
                cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationStats', [
                            json_obj1, date_insert, None])
                conn.commit()

                # json_obj2 = json.dumps(chunk2)
                # cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
                #             json_obj2, None])
                # conn.commit()
        cur.close()
        conn.close()

    except Exception as err:
        # print(err)
        logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
        message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
        SendLogTelegram.send_message(message_telegram)
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
        # print(err)
        logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
        message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
        SendLogTelegram.send_message(message_telegram)
        raise ValueError
  

if __name__ == "__main__":

    date_insert='2021-03-23'
    with open(os.path.join(root, cus_dict_fn), 'rb') as g:
        daily_cus_dict = pickle.load(g)
    with open(os.path.join(root, cus_list_fn), 'rb') as f:
        CUST_LIST = pickle.load(f)

    # build batches
    CUST_LIST = np.sort(CUST_LIST)
    for cus in CUST_LIST:
        if cus==1889290:
            print('1889290 in CUST_LIST')
        # else:
        #     print('No 1889290 in CUST_LIST')
    # BATCHES = [CUST_LIST[x:x+10] for x in range(0, len(CUST_LIST), 10)]

    # aggregate((np.min(BATCHES[0]),np.max(BATCHES[0])))
    # pool = mp.Pool(nb_workers_phase_2)
    # for _ in tqdm(pool.imap_unordered(aggregate, [(np.min(BATCH), np.max(BATCH),0,date_insert,daily_cus_dict) for BATCH in BATCHES]), total=len(BATCHES), desc='AGG'):
    #     pass
    # with ProcessPoolExecutor(max_workers=nb_workers_phase_2) as executor:
    #     canvas=[executor.submit(aggregate,(np.min(BATCH), np.max(BATCH),date_insert,daily_cus_dict)) for BATCH in BATCHES]
    #     results=[]
    #     for f in as_completed(canvas):
    #         results+=f.result()
            # print(f.result())
    
    # print('HEAD DF',pd.DataFrame(results).head(),sep='\n')
    # pool = mp.Pool(nb_workers_phase_2)
    # for _ in tqdm(pool.imap_unordered(day_end_aggregate, [(np.min(BATCH), np.max(BATCH),results) for BATCH in BATCHES]), total=len(BATCHES), desc='DAY-END AGG'):
    #     pass