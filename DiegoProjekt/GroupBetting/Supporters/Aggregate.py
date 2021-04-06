import sys
sys.path.append('C:/Users/diego.nguyen/diegoProj/GroupBetting')
import pandas as pd
import numpy as np
from Configuration.LocalConfiguration import LocalConfiguration
from Configuration.ProConfiguration import ProConfiguration

ENV='LOCAL'

if ENV=='LOCAL':

    config = LocalConfiguration()

else:
    config = ProConfiguration()

percent_score = int(config.getPercentScore(config))
combination_threshold = int(config.GetCombinationThreshold(config))

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

def transform_to_list(df):
    keys, values1, values2 = df.sort_values('sample_id').values.T
    ukeys, index = np.unique(keys, True)
    arrays = np.split(values1, index[1:])
    arrays2 = np.split(values2, index[1:])
    df2 = pd.DataFrame({'sample_id': ukeys, 'ML': [list(
        a) for a in arrays], 'BL': [list(b) for b in arrays2]})
    return df2

def aggregate(df,mode,the_first_is_the_last=False):
    """
    >>> Input   :   df                      : dataframe
                    mode                    : string
                    the_first_is_the_last   : boolean | default : False
    >>> Output  :   (df_byAI,df_byAISPU)                        if mode is OnTheFly
                    (df_susinfo,df_byAI,df_byAISPU)             if mode is NewData
                    (df_result3,df_byAI,df_byAISPU)             if mode is DayEnd and the_first_is_the_last is False
                    (df_result3,df_susinfo,df_byAI,df_byAISPU)  if mode is DayEnd and the_first_is_the_last is True
    """
    
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
    if mode=='NewData' or the_first_is_the_last:
        susinfo = df[['sample_id', 'ML', 'BL']]
        df_susinfo = transform_to_list(susinfo)
        df_susinfo = df_susinfo.set_index('sample_id')
        df_susinfo['ML'] = [','.join(map(str, l)) for l in df_susinfo['ML']]
        df_susinfo['BL'] = [','.join(map(str, l)) for l in df_susinfo['BL']]
        df_resultinfo = pd.merge(df_custid, df_susinfo, left_index=True, right_index=True)

    df_result3 = df_result3.drop(columns=['minor', 'major'])

    # add BC column with default value 1
    df_result3['BC'] = 1
    df_result3['TJD'] = 1
    # print('df_result3',df_result3.head(),sep='\n')
    # aggreagate without history data
    df_result3['S'] = 100 * (df_result3['TS'] + df_result3['MS'] + df_result3['LS']) / 3

    df_byAISample03 = df_result3[['C1', 'C2', 'S','TJSC']]
    df_byAI = df_byAISample03[(df_byAISample03['S'] >= percent_score) & (
        df_byAISample03['TJSC'] >= combination_threshold)]
    
    df_byAISPU = pd.DataFrame()
    isTraceLog = False
    if len(df_byAI.index) != 0:
        isTraceLog = True
        df_result4 = df_result3[['TS', 'MS', 'LS', 'TJD', 'TJC']]
        df_byAISPU = pd.merge(df_result4, df_byAI,left_index=True, right_index=True)
    if mode=='NewData':
        return (df_resultinfo,df_byAI,df_byAISPU,isTraceLog)
    elif mode=='OnTheFly':
        return (df_byAI,df_byAISPU,isTraceLog)
    else:
        if the_first_is_the_last:
            return (df_result3,df_resultinfo,df_byAI,df_byAISPU,isTraceLog)
        else:
            return (df_result3,df_byAI,df_byAISPU,isTraceLog)