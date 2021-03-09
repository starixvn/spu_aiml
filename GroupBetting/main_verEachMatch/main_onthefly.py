import pandas as pd
import numpy as np
import multiprocessing as mp

import logging
import csv
import json
import warnings
import helper
import SendLogTelegram
import agg
import datetime
import time
import pickle
import itertools
import gc
import os
import torch

from tqdm import tqdm
from pandarallel import pandarallel
# from sklearn.metrics import pairwise_distances
from mysql.connector import MySQLConnection
from Configuration.Configuration import Configuration
from datetime import date

warnings.filterwarnings("ignore")

config = Configuration()

# define log config
save_dir_log = config.GetSaveDirectoryModel(config)
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
root = "/home/vnteam/Data/MatchData/"
root_orig = "/home/vndata4ai/"
# orig_fn="bettrans_01_31_2021.csv"
mjl_fn = "major_league.csv"
mlm_fn = "match20201129.csv"
output1a = "/home/vnteam/Data/SaveData/output1a/"
output1b = "/home/vnteam/Data/SaveData/output1b/"
result_fn = "baseline_results.csv"
match_breaking = 'match_breaking'
cus_list_fn = 'cus_list.pkl'
cus_dict_fn = 'cus_dict.pkl'
mlm_dict_fn = 'match_league_map.pkl'


# define chunk_size for DB saving
chunk_size = 100000

# define nb_workers_phase_1
nb_workers_phase_1 = 8

# define batch_size
batch_size = 1000000

# define nb_workers_phase_2
nb_workers_phase_2 = 24


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


def process_a_combination(filepath):
    """
    >>> Input    :  filepath
    >>> Output   :  pairwise-time-score matrix
    """

    # get match - bettype - league
    match = int(filepath.split('.')[0].split('_')[0])
    bettype = int(filepath.split('.')[0].split('_')[1])

    # read data of a (match,bettype) - combination
    MATCH = pd.read_csv(os.path.join(root, match_breaking, filepath))

    # pick up customer list and sort it
    CUST_LIST = np.sort(MATCH.custid.unique())

    # get the maximum of number of tickets
    maxlen = MATCH.groupby('custid').count()['transdate'].max()

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
        #{"C1":int(CUST_LIST[i]),"C2":int(CUST_LIST[j]),"TS": m[i,j], "M":match,"B":bettype,"L":league,"TJC":count_joining_combs(int(CUST_LIST[i]),int(CUST_LIST[j])),"IML":is_major}

        #{"C1":int(CUST_LIST[i]),"C2":int(CUST_LIST[j]),"TS": m[i,j], "M":match,"B":bettype,"L":league,"TJC":type(count_joining_combs(CUST_LIST[i],CUST_LIST[j])),"IML":is_major}

        {"C1": int(CUST_LIST[i]), "C2":int(
            CUST_LIST[j]), "TS": m[i, j], "M":match, "B":bettype, "L":1, "TJC":1, "IML":1}

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
            conn = MySQLConnection(user='aimlServiceAdmin', password='aimlServiceAdmin@AIML2209#',
                                   host='10.40.40.78', port='3306', database='SPU_AIML')
            cursor = conn.cursor()
            for chunk in chunks:
                jsonList = json.dumps(chunk)
                cursor.callproc(
                    'SPU_AIML_InsertAssociationStatsStaging', [jsonList, None])
                conn.commit()
            cursor.close()
            conn.close()
        except Exception as err:
            print(err)
    print("\n", "MATCH %.0f BETTYPE %.0f HAVING SHAPE %.0f SAVING TAKES %.0f SECONDS" % (
        match, bettype, len(CUST_LIST), time.time() - start_save))
    del chunks, obj
    gc.collect()


def count_joining_combs(cus1, cus2):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(cus_dict[cus1]), set(cus_dict[cus2])
    return len(comb_a.intersection(comb_b))


def is_major(x):
    major_or_minor = match_league_map[x]
    if 'major' in major_or_minor:
        return 1
    else:
        return 0


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


def compute_league_score(list_minor=None, list_major=None):

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


def total_leaguescore(x, y):
    if y == 1:
        return (x + 5/2) * (2/7)
    elif x == 1:
        return (y + 3/2) * (2/5)
    elif y != 1 and x != 1:
        minor_score = (x + 5/2) * (2/7)
        major_score = (y + 3/2) * (2/5)
        return (3 * (minor_score + 1) + (major_score + 2)) * (1/9)


def aggregate(args):
    try:
        conn = MySQLConnection(user='aimlServiceAdmin', password='aimlServiceAdmin@AIML2209#',
                               host='10.40.40.78', port='3306', database='SPU_AIML')
        cur = conn.cursor()
        cur.callproc('SPU_AIML_GetAssociationStatsStaging',
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
            "AccTS",
            "AccMS",
            "AccLS",
            "AccTJD"])
        #time_readfile = time.time()
        # fill none to 0
        df['AccTS'].fillna(0, inplace=True)
        df['AccMS'].fillna(0, inplace=True)
        df['AccLS'].fillna(0, inplace=True)
        df['AccTJD'].fillna(0, inplace=True)

        # print(df.head())
        # print(df['IsMajorLeague'].unique)
        df['IsMajorLeague'] = df['ML'].apply(lambda z: is_major(z))
        df['TJC'] = df.apply(
            lambda z: count_joining_combs(z['C1'], z['C2']), axis=1)
        # print(df.head())
        first_time = time.time()
        df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)

        first_time = time.time()
        df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)

        df = df.astype({"sample_id": 'int64'})
        df['TS'] = df['TS'].astype('float')
        df['AccTS'] = df['AccTS'].astype('float')
        df['AccMS'] = df['AccMS'].astype('float')
        df['AccLS'] = df['AccLS'].astype('float')
        # print(df.info())
        #start_time = time.time()
        # print('Complete read file and clean data: ', time.time() - time_readfile)
        # print('-------------------------------------------------------')
        # print('Start Algorithm')
        # print('-------------------------------------------------------')

        df_custid = pd.DataFrame()
        df_custid = df.groupby('sample_id')[['C1', 'C2', 'TJC']].first()
        # df_custid.apply(pd.DataFrame)
        # print(df_custid.head())
        #print('----------finish custid: ', time.time() - start_time)

        #start_time = time.time()
        df_leaguescore = pd.DataFrame()
        #print('-----group leaguescore')

        # version 1
        #df_leaguescore = (df.groupby(['sample_id','IsMajorLeague', 'ML']).size().groupby(level=[0,1]).agg(list).unstack('IsMajorLeague'))

        # version 2
        # df_leaguescore = (df.groupby(['sample_id','IsMajorLeague'])['ML'].apply(lambda x: x.value_counts().agg(list)).unstack('IsMajorLeague',fill_value = []))
        # df_leaguescore = (df.groupby(['sample_id','IsMajorLeague'])['ML'].agg(lambda x: list(x.value_counts())).unstack('IsMajorLeague',fill_value = []))
        # if 1 not in df_leaguescore:
        #     df_leaguescore[1] = [list() for x in range(len(df_leaguescore.index))]
        # if 0 not in df_leaguescore:
        #     df_leaguescore[0] = [list() for x in range(len(df_leaguescore.index))]

        # print(df_leaguescore.head())
        # version 3
        # keys = df['sample_id'].astype(str) + '_' + df['IsMajorLeague'].astype(str)
        # df_parameter = (df.groupby(keys)['ML'].apply(lambda x: x.value_counts().agg(list)))
        #print('------finish group league: ', time.time() - start_time)

        # version 4
        df_parameter = (df.groupby(['sample_id', 'IsMajorLeague', 'ML']).size(
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
        #print('------calculate league score')
        #df_leaguescore['League_Score'] = df_leaguescore.apply(lambda x: compute_league_score(x[0],x[1]), axis = 1)
        #df_leaguescore['League_Score'] = compute_league_score(df_leaguescore[0],df_leaguescore[1])
        #print('----------finish leaguescore: ', time.time() - start_time)

        #start_time = time.time()
        df_timescore = df.groupby('sample_id')[['TS']].mean()
        #print('----------finish timescore: ', time.time() - start_time)

        #start_time = time.time()
        df_matchscore = pd.DataFrame()
        df_matchscore['TJSC'] = df.groupby(['sample_id', 'ML'])[
            'BL'].nunique().groupby('sample_id').sum()
        df_matchscore['MS'] = df_matchscore['TJSC'] / df_custid['TJC']
        #print('----------finish matchscore: ', time.time() - start_time)

        #start_time = time.time()
        df_result = pd.merge(df_custid, df_timescore,
                             left_index=True, right_index=True)
        df_result2 = pd.merge(df_result, df_matchscore,
                              left_index=True, right_index=True)
        # print(df_result2.head())
        df_result3 = pd.merge(df_result2, df_leaguescore,
                              left_index=True, right_index=True)
        #print('----------finish merge: ', time.time() - start_time)

        # print(df_result3.info())
        # print(df_result3.head())

        # get suspicious info
        start_time = time.time()
        susinfo = df[['sample_id', 'ML', 'BL']]
        df_susinfo = transform_to_list(susinfo)
        df_susinfo = df_susinfo.set_index('sample_id')
        df_susinfo['ML'] = [','.join(map(str, l)) for l in df_susinfo['ML']]
        df_susinfo['BL'] = [','.join(map(str, l)) for l in df_susinfo['BL']]
       # print('----------finish merge: ', time.time() - start_time)
        df_resultinfo = pd.merge(
            df_custid, df_susinfo, left_index=True, right_index=True)

        #print('----------finish TOTAL TIME: ', time.time() - first_time)

        # print(df_result3.head())
        # move to dba
        df_result3 = df_result3.drop(columns=['minor', 'major'])

        #df_result3['TJD'] = 1
        df_result3['BC'] = 1

        ###
        # print(df_resultinfo.head())
        df_resultinfo = df_resultinfo.drop(columns=['TJC'])

        # table By AI
        df_sampleDailyScore = df[['sample_id', 'C1',
                                  'C2', 'AccTS', 'AccMS', 'AccLS', 'AccTJD']]
        df_DailyScore = df_sampleDailyScore.groupby('sample_id').first()
        # print(df_DailyScore)
        # print(abc.head())
        df_DailyScore['AccTS'] = df_DailyScore['AccTS'] + df_result3['TS']
        df_DailyScore['AccMS'] = df_DailyScore['AccMS'] + df_result3['MS']
        df_DailyScore['AccLS'] = df_DailyScore['AccLS'] + df_result3['LS']
        df_DailyScore['AccTJD'] += 1

        df_result3['TS'] = df_DailyScore['AccTS']
        df_result3['MS'] = df_DailyScore['AccMS']
        df_result3['LS'] = df_DailyScore['AccLS']
        df_result3['TJD'] = df_DailyScore['AccTJD']

        df_DailyScore['S'] = 100 * (df_DailyScore['AccTS'] + df_DailyScore['AccMS'] *
                                    df_DailyScore['AccLS']) / (df_DailyScore['AccTJD']*(df_DailyScore['AccTJD'] + 1))

        df_DailyScore = df_DailyScore.drop(
            columns=['AccTS', 'AccMS', 'AccLS', 'AccTJD'])

        df_byAISample01 = df_result3['TJSC']
        df_byAISample02 = df_DailyScore[['C1', 'C2', 'S']]
        df_byAISample03 = pd.merge(
            df_byAISample02, df_byAISample01, left_index=True, right_index=True)
        df_byAI = df_byAISample03[(df_byAISample03['S'] >= percent_score) & (
            df_byAISample03['TJSC'] >= combination_threshold)]
        # print(df_result3.head())
        # print(args[0])
        # print(args[1])
        # move to dba

        fulldata_dba = df_result3.to_dict(orient="records")
        fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
        fulldataDailyScore_dba = df_DailyScore.to_dict(orient="records")
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")

        chunks1 = [fulldata_dba[x:x+chunk_size]
                   for x in range(0, len(fulldata_dba), chunk_size)]

        chunks2 = [fulldatainfo_dba[x:x+chunk_size]
                   for x in range(0, len(fulldatainfo_dba), chunk_size)]

        chunks3 = [fulldataDailyScore_dba[x:x+chunk_size]
                   for x in range(0, len(fulldataDailyScore_dba), chunk_size)]

        chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                   for x in range(0, len(fulldatabyAI_dba), chunk_size)]

        try:
            conn = MySQLConnection(user='aimlServiceAdmin', password='aimlServiceAdmin@AIML2209#',
                                   host='10.40.40.78', port='3306', database='SPU_AIML')
            cur = conn.cursor()
            for (chunk1, chunk2, chunk3) in zip(chunks1, chunks2, chunks3):
                json_obj1 = json.dumps(chunk1)
                cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationStats', [
                             json_obj1, date_insert, None])
                conn.commit()

                json_obj2 = json.dumps(chunk2)
                cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
                             json_obj2, None])
                conn.commit()

                json_obj3 = json.dumps(chunk3)
                cur.callproc('SPU_AIML.SPU_AIML_InsertDailyScore',
                             [json_obj3, None])
                conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            print(err)
            logging.error(f'Error insert 3 table in DBA: {err}')
            message_telegram = f'Error insert 3 table in DBA: {err}'
            SendLogTelegram.send_message(message_telegram)

        # insert dba CTS
        try:
            conn = MySQLConnection(user='ctsServiceAdmin', password='ctsServiceAdmin@CTS2209#',
                                   host='10.40.40.58', port='3306', database='CTS_DataCenter')
            cur = conn.cursor()
            for chunk4 in chunks4:
                json_obj4 = json.dumps(chunk4)
                cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [
                             json_obj4, date_insert, None])
                conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            print(err)
            logging.error(f'Error insert table byAI in DBA CTS: {err}')
            message_telegram = f'Error insert table byAI in DBA CTS: {err}'
            SendLogTelegram.send_message(message_telegram)
    except Exception as err:
        print(err)
        logging.error(f'Error in agg function: {err}')
        message_telegram = f'Error in agg function: {err}'
        SendLogTelegram.send_message(message_telegram)


if __name__ == "__main__":
    while True:
        check_files = [f for f in os.listdir(root_orig)]
        if len(check_files) > 0:
            #os.system('source env/bin/activate')
            orig_fn = check_files[0]
            time_begin = time.time()
            today = date.today()
            logging.info(
                "======================================================================================================")
            logging.info(f"Running for Date: {today}")

            message_telegram = f"Group Betting is running for {today}"
            SendLogTelegram.send_message(message_telegram)
            

            # Truncate table StatsStaging
            try:
                conn = MySQLConnection(user='aimlServiceAdmin', password='aimlServiceAdmin@AIML2209#',
                                    host='10.40.40.78', port='3306', database='SPU_AIML')
                cur = conn.cursor()
                # Truncate table DailyScore
                cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
                            ['AssociationStatsStaging'])
                conn.commit()
            except Exception as err:
                print(err)
                logging.error(
                    f"Error Truncate Table AssociationStatsStaging in DBA phase 2: {err}")
                message_telegram = f"Error Truncate Table AssociationStatsStaging in DBA phase 2: {err}"
                SendLogTelegram.send_message(message_telegram)
                break

            # START PHASE 0 --> PREPARATION
            # *****************************************************************************************************************************************************************************
            # print what time it is now !
            try:
                time_phase0 = time.time()
                t = time.localtime()
                current_time = time.strftime("%H:%M:%S", t)
                print("CURRENT TIME :", current_time, '\n')

                # read - filter - preprocess data
                data = pd.read_csv(os.path.join(root_orig, orig_fn),
                                encoding='ISO-8859-1', skiprows=[1], skipfooter=1)
                DATE = data[(data.bettype.isin([1, 3, 7, 8]))
                            & (data.liveindicator)]

                date_winlost = DATE['winlostdate'].min()
                DATE = DATE[['custid', 'matchid', 'transdate', 'bettype']]
                date = DATE['transdate'].min()
                date_insert = date_winlost.split()[0]
                # date_insert='2021-01-29'
                print(f"date insert {date_insert}")
                DATE['transdate'] = DATE['transdate'].apply(
                    lambda z: distance_time(separate(date), separate(z)))

                # get list of matches
                matches = DATE.matchid.unique()
                LS = DATE.custid.unique()
                with open(os.path.join(root, cus_list_fn), 'wb') as f:
                    pickle.dump(LS, f)

                # build match_league_map
                data['category'] = data['category'].str.lower()
                data['category'] = data['category'].fillna(value='minor')
                match_league_map = data[['matchid', 'category']].drop_duplicates().set_index("matchid")[
                    "category"].to_dict()
                with open(os.path.join(root, mlm_dict_fn), 'wb') as f:
                    pickle.dump(match_league_map, f)

                # match breaking
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
                with open(os.path.join(root, cus_dict_fn), 'wb') as f:
                    pickle.dump(cus_dict, f)
                print('\n', f"LEN OF CUS DICT {len(cus_dict)}")
                logging.info(
                    f"Done phase 0, takes {time.time() - time_phase0} seconds")
                # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
            except Exception as e:
                logging.error(f"Error at phase 0: {e}")
                message_telegram = f"Error at phase 0: {e}"
                SendLogTelegram.send_message(message_telegram)
                break

            # END PHASE 0 - START PHASE 1
            # ****************************************************************************************************************************************************************************
            try:
                start_processing = time.time()

                candidates = os.listdir(os.path.join(root, match_breaking))
                pool = mp.Pool(8)
                # pool.map(process_a_combination,candidates)
                # process_a_combination('39960404_3.csv')
                for _ in tqdm(pool.imap_unordered(process_a_combination, candidates), total=len(candidates), desc='MAIN PROCESS'):
                    pass
                print('\n', '********************************************************************************************************************************************')
                print("\n", "PROCESSING TIME %.0f SECONDS" %
                    (time.time() - start_processing))
                logging.info(
                    f"Done phase 1, takes {time.time() - start_processing} seconds")
            except Exception as e:
                logging.error(f"Error phase 1: {e}")
                message_telegram = f"Error phase 1: {e}"
                SendLogTelegram.send_message(message_telegram)
                break

            # END PHASE 1 - START PHASE 2
            # *****************************************************************************************************************************************************************************
            try:
                start_time = time.time()
                # date_insert='2021-01-29'
                # read customer list
                with open(os.path.join(root, cus_list_fn), 'rb') as f:
                    CUST_LIST = pickle.load(f)

                with open(os.path.join(root, cus_dict_fn), 'rb') as f:
                    cus_dict = pickle.load(f)

                with open(os.path.join(root, mlm_dict_fn), 'rb') as f:
                    match_league_map = pickle.load(f)

                # build batches
                CUST_LIST = np.sort(CUST_LIST)
                BATCHES = [CUST_LIST[x:x+10] for x in range(0, len(CUST_LIST), 10)]

                # read match-league map data and major league info data
                # aggregate((np.min(BATCHES[0]),np.max(BATCHES[0])))
                # connect DBs

                try:
                    conn = MySQLConnection(user='aimlServiceAdmin', password='aimlServiceAdmin@AIML2209#',
                                        host='10.40.40.78', port='3306', database='SPU_AIML')
                    cur = conn.cursor()
                    # Truncate table DailyScore
                    cur.callproc(
                        'SPU_AIML.SPU_AIML_DBA_Truncate_Table', ['DailyScore'])
                    conn.commit()
                except Exception as err:
                    print(err)
                    logging.error(
                        f"Error Truncate Table DailyScore in DBA phase 2: {err}")
                    message_telegram = f"Error Truncate Table DailyScore in DBA phase 2: {err}"
                    SendLogTelegram.send_message(message_telegram)
                    break

                # aggregate((np.min(BATCHES[0]),np.max(BATCHES[0])))
                pool = mp.Pool(24)
                for _ in tqdm(pool.imap_unordered(aggregate, [(np.min(BATCH), np.max(BATCH)) for BATCH in BATCHES]), total=len(BATCHES), desc='AGG'):
                    pass

                # agg final table
                try:
                    conn = MySQLConnection(user='aimlServiceAdmin', password='aimlServiceAdmin@AIML2209#',
                                        host='10.40.40.78', port='3306', database='SPU_AIML')
                    cur = conn.cursor()
                    # update table SystemParameter
                    cur.callproc('SPU_AIML.SPU_AIML_UpdateScanStatus',
                                [date_insert, None])
                    conn.commit()

                    cur.close()
                    conn.close()
                    print("***********************************************************************************************************************************************************************************")
                    print("AGG & INSERT TIME %.0f SECONDS" %
                        (time.time() - start_time))
                    logging.info(
                        f"Done phase 2, takes {time.time() - start_time} seconds")
                    message_telegram = f"Group Betting is done, total {round((time.time() - time_begin)/3600,4)} hours "
                    SendLogTelegram.send_message(message_telegram)
                except Exception as err:
                    print(err)
                    logging.error(
                        f"Error insert UpdateScanStatus table in DBA phase 2: {err}")
                    message_telegram = f"Error insert UpdateScanStatus table in DBA phase 2: {err}"
                    SendLogTelegram.send_message(message_telegram)
                    break
            except Exception as e:
                logging.error(f"Error phase 2: {e}")
                message_telegram = f"Error phase 2: {e}"
                SendLogTelegram.send_message(message_telegram)
                break
            
            # remove file when complete
            os.remove(root_orig + orig_fn)
            
        else:
            time.sleep(time_sleep)
    
