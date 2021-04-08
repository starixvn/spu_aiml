import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from GroupBetting.Support import SendLogTelegram
import numpy as np
import pandas as pd
import datetime
import logging
def notify_logging(mess, isInfo = False):
    if isInfo:
        logging.info(mess)
    else:
        logging.error(mess)
    SendLogTelegram.send_message(mess)
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

def count_joining_combs_by_file_cus_dict(cus1,cus2,batch_cus_dict):
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
    
def leaguescore_dataflow(df):
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
    return df_leaguescore

def data_suspiciousInfo(df):
    susinfo = df[['sample_id', 'ML', 'BL']]
    df_susinfo = transform_to_list(susinfo)
    df_susinfo = df_susinfo.set_index('sample_id')
    df_susinfo['ML'] = [','.join(map(str, l)) for l in df_susinfo['ML']]
    df_susinfo['BL'] = [','.join(map(str, l)) for l in df_susinfo['BL']]
    return df_susinfo

def GroupBetting_FeatureScore(df,config,isCreateSusInfo = False,isDayEnd = False):
    df_custid = pd.DataFrame()
    df_custid = df.groupby('sample_id')[['C1', 'C2', 'TJC']].first()

    # calculate League Score
    df_leaguescore = leaguescore_dataflow(df)
    
    # calculate Time Score
    df_timescore = df.groupby('sample_id')[['TS']].mean()

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
    df_resultinfo = pd.DataFrame()
    if isCreateSusInfo:
        df_susinfo = data_suspiciousInfo(df)
        df_resultinfo = pd.merge(df_custid, df_susinfo, left_index=True, right_index=True)
    
    
    
    df_result3 = df_result3.drop(columns=['minor', 'major'])

    # add BC column with default value 1
    if isDayEnd:
        df_result3['BC'] = 1
        df_result3['TJD'] = 1
    # aggreagate without history data
    df_result3['S'] = 100 * (df_result3['TS'] + df_result3['MS'] + df_result3['LS']) / 3

    df_byAISample03 = df_result3[['C1', 'C2', 'S','TJSC']]
    df_byAI = df_byAISample03[(df_byAISample03['S'] >= config.percent_score) & (
        df_byAISample03['TJSC'] >= config.combination_threshold)]
            
    isTraceLog = False
    df_byAISPU = pd.DataFrame()
    if len(df_byAI.index) != 0:
        isTraceLog = True
        df_result4 = df_result3[['TS', 'MS', 'LS', 'TJD', 'TJC']]
        df_byAISPU = pd.merge(df_result4, df_byAI,
                            left_index=True, right_index=True)
    return df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3