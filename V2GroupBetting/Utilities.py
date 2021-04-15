from numba.core import config
import pandas as pd
import datetime
import os
import gc
# import time
import pickle
import itertools
import numpy as np
from tqdm.std import tqdm
from numba import prange, njit, set_num_threads
# from mysql.connector import MySQLConnection

from DataAccess import GroupBettingDataAccess,CommonDataAccess

def load_a_file(location,file_name):
    # location,file_name = args
    with open(os.path.join(location, file_name), 'rb') as f:
        my_file = pickle.load(f)
    return my_file

def save_a_file(location,file_name,object):
    with open(os.path.join(location, file_name), 'wb') as f:
        pickle.dump(object,f)

def remove_files(location,*file_names):
    # check_cus_files=os.listdir(location)
    try:
        for file_name in file_names:
            os.remove(os.path.join(location,file_name))
    # if cus_dict_fn in check_cus_files:
    #     os.remove(os.path.join(root,cus_dict_fn))
    except:
        pass

def check_files(location,initial,day_prev):
    check_files = [f for f in sorted(os.listdir(location))]
    if len(check_files)==0:
        # time.sleep(time_sleep)
        return None
    orig_fn = check_files[0]
    # month_curr=orig_fn.split('.')[0].split('_')[1]
    day_curr = orig_fn.split('.')[0].split('_')[2]
    initial.append(day_curr)
    # year_curr=orig_fn.split('.')[0].split('_')[3]
    time_constant=int(day_curr)-int(day_prev)
    return initial,time_constant

def decompose_into_combinations(location,decomposed_folder,data):
    check_match_files=os.listdir(os.path.join(location, decomposed_folder))
    if len(check_match_files)>0:
        for fn in check_match_files:
            os.remove(os.path.join(location, decomposed_folder, fn))
    # for n in tqdm(range(len(matches)), desc="MATCH BREAKING"):
    # get list of matches
    matches = data.matchid.unique()
    # print(f'Number of matches {len(matches)}')
    for n in range(len(matches)):
        match = matches[n]
        m = data[data.matchid == match]
        for bt in [1, 3, 7, 8]:
            f = m[m.bettype == bt]
            if f.custid.nunique() > 1:
                f.to_csv(os.path.join(location, decomposed_folder,
                                    f"{match}_{bt}.csv"), index=False)

def build_batch_cus_dict(location,decomposed_folder):
    batch_cus_dict = {}
    list_of_matches = os.listdir(os.path.join(location, decomposed_folder))
    # for k in tqdm(range(len(list_of_matches)), desc="BUILD CUS DICT"):
    for k in range(len(list_of_matches)):
        fn = list_of_matches[k]
        match, bt = int(fn.split('.')[0].split('_')[0]), int(
            fn.split('.')[0].split('_')[1])
        df = pd.read_csv(os.path.join(location, decomposed_folder, fn))

        ls = df.custid.unique()
        for cus in ls:
            if cus not in batch_cus_dict:
                batch_cus_dict[cus] = [(match, bt)]
            else:
                batch_cus_dict[cus].append((match, bt))
    return batch_cus_dict

def build_daily_cus_dict(location, file_name, batch_cus_dict):
    check_cus_files = os.listdir(os.path.join(location))
    if file_name not in check_cus_files:
        save_a_file(location, file_name, batch_cus_dict)
        return batch_cus_dict
    else:
        daily_cus_dict = load_a_file(location, file_name)
        for key,value in batch_cus_dict.items():
            if key not in daily_cus_dict:
                daily_cus_dict[key] = value
            else:
                daily_cus_dict[key] += value
        save_a_file(location, file_name ,daily_cus_dict)
        # print('\n', f"LEN OF CUS DICT {len(batch_cus_dict)}")
        daily_cus_dict = load_a_file(location, file_name)
        return daily_cus_dict

def build_daily_cus_list(location, file_name, batch_cus_list):
    check_cus_files=os.listdir(os.path.join(location))
    if file_name not in check_cus_files:
        save_a_file(location, file_name, batch_cus_list)
        return batch_cus_list
    else:
        daily_cus_list = load_a_file(location, file_name)
        daily_cus_list += batch_cus_list
        daily_cus_list = list(set(daily_cus_list))
        save_a_file(location, file_name, daily_cus_list)
        return daily_cus_list


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

def build_data(args):
    list_file,config = args
    data =  pd.concat([pd.read_csv(os.path.join(config.root_orig, list_file[idx]),
                                encoding = 'ISO-8859-1'
                                , skiprows=[1], skipfooter=1
                                ).assign(file_name = list_file[idx]) for idx in tqdm(range(len(list_file)),desc = 'Combining Files')], ignore_index = True)
    for file in list_file:
        os.rename(os.path.join(config.root_orig, file),os.path.join(config.backup, file))
    return data

def count_joining_combs(cus1, cus2,cusDict):
    """
    >>> Input   : cus1,cus2
    >>> Output  : number of joining combinations
    """
    comb_a, comb_b = set(cusDict[cus1]), set(cusDict[cus2])
    return len(comb_a.intersection(comb_b))

@njit(parallel=True)
def compute_pairwise_cus(X,time_threshold,n_jobs=4):
    set_num_threads(n_jobs)
    n = X.shape[0]
    mat = np.empty((n, n), np.float64)
    
    for i in prange(n-1):
        for j in range(i+1, n):
            mat[i, j] = mat[j, i] = calculate_difference(X[i], X[j], time_threshold)

    np.fill_diagonal(mat, 0.0)   
    return mat
    
@njit
def calculate_difference(ls1, ls2, time_threshold):
    # drop trash
    ls1 = ls1[ls1 != -1]
    ls2 = ls2[ls2 != -1]
    
    '''reshape to [[transdate, custID],
                [],
                ...]
    '''
    ls1 = ls1.reshape(-1, 2)
    ls2 = ls2.reshape(-1, 2)
    
    STACK = np.vstack((ls1, ls2))
    SORT = STACK[STACK[:,0].argsort()]
    
    time_arr,cus_arr = SORT.T
    
    diff_cus = cus_arr[1:]-cus_arr[:-1]
    #zip_trans = np.column_stack((trans_arr[1:],trans_arr[:-1]))
    zip_time = np.column_stack((time_arr[1:],time_arr[:-1]))

    #eff_trans = zip_trans[(diff_cus != 0) & (diff_time < 20)].flatten().astype(np.int64)
    eff_zip_time = zip_time[diff_cus != 0]
    #fil_cus_tickets = diff_time[diff_cus != 0]
    #eff_diff_time = fil_cus_tickets[fil_cus_tickets < 20]
    diff_time=eff_zip_time[:,0]-eff_zip_time[:,1]
    eff_diff_time=diff_time[diff_time<=20]
    if len(eff_diff_time)==0:
        time_score = 0
    else:
        time_score = (time_threshold-np.mean(eff_diff_time)) / time_threshold

    #return (time_score, set(list(eff_trans)))
    return time_score

class ExtractInsightsFromData():
    
    def extract_insights_from_data(args):
        """
        >>> Input    :  filepath,batch_cus_dict
        >>> Output   :  pairwise-time-score matrix
        """
        filepath,batch_cus_dict,config = args
        # get match - bettype - league
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
        # start_compute = time.time()
        m = compute_pairwise_cus(X, config.time_threshold)
        #print("\n","PAIRWISE MATRIX HAVING SHAPE %s OF MATCH %.0f BETTYPE %.0f :" % (m.shape,match,bettype),m,sep='\n')
        # print("\n", "MATCH %.0f BETTYPE %.0f | %.0f CUSTOMERS | COMPUTING TIME SCORE TAKES %.0f SECONDS" % (
        #     match, bettype, len(COMBINATION_CUST_LIST), time.time() - start_compute))
        del X, MATCH
        gc.collect()

        # build up result object which is a list of dictionaries whose values are positive time score
        # start_transform = time.time()

        obj = [

            {"C1": int(COMBINATION_CUST_LIST[i]), "C2":int(COMBINATION_CUST_LIST[j]), "TS": m[i, j], "M":match, "B":bettype
                , "L":int(leagueid)
                , "TJC":count_joining_combs(COMBINATION_CUST_LIST[i], COMBINATION_CUST_LIST[j],batch_cus_dict)
                , "IML":IMJ
                ,  "IN":1}

            for (i, j) in itertools.combinations([x for x in range(len(COMBINATION_CUST_LIST))], 2) if m[i, j] > 0
        ]
        # print(f"JSON OBJ 1th {obj[0]}",f"JSON OBJ 2nd {obj[1]}",f"JSON OBJ 3rd {obj[2]}",sep='\n')

        # start_save = time.time()
        # build chunks for DB saving
        # chunks = [obj[x:x+config.chunk_size] for x in range(0, len(obj), config.chunk_size)]
        del m
        #print("JSON OBJECT :",obj,sep="\n")
        # print("\n", "MATCH %.0f BETTYPE %.0f | %.0f CUSTOMERS | TRANSFROMING TAKES %.0f SECONDS" % (
        #     match, bettype, len(COMBINATION_CUST_LIST), time.time() - start_transform))

        GroupBettingDataAccess.insert_association_stats_staging((pd.DataFrame(obj),config))

class Aggregate():

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

    def total_leaguescore(x,y):
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

    def transform_dataframe_to_support_aggregate(df ,mode, the_first_is_the_last, config):
        """
        >>> Input   :   df                      : dataframe
                        mode                    : string
                        the_first_is_the_last   : boolean
                        config                   
        >>> Output  :   (df_byAI,df_byAISPU)                        if mode is OnTheFly
                        (df_susinfo,df_byAI,df_byAISPU)             if mode is NewData
                        (df_result3,df_byAI,df_byAISPU)             if mode is DayEnd and the_first_is_the_last is False
                        (df_result3,df_susinfo,df_byAI,df_byAISPU)  if mode is DayEnd and the_first_is_the_last is True
        """
        # df ,mode, the_first_is_the_last, config = args
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
            lambda x: Aggregate.total_leaguescore(x['minor'], x['major']), axis=1)
        
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
            df_susinfo = Aggregate.transform_to_list(susinfo)
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
        df_byAI = df_byAISample03[(df_byAISample03['S'] >= config.percent_score) & (
            df_byAISample03['TJSC'] >= config.combination_threshold)]
        
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

    def aggregate(args):
        BATCH, date_insert, daily_cus_dict, the_first_is_the_last, config = args
        df = GroupBettingDataAccess.get_association_stats_staging((BATCH,config))
        df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
        df = df.astype({"sample_id": 'int64'})
        df['TS'] = df['TS'].astype('float')
        IsNewdf=df[df.IsNew==1]
        if len(IsNewdf)>0:
            df_resultinfo,df_byAI,df_byAISPU,isTraceLog = Aggregate.transform_dataframe_to_support_aggregate(IsNewdf, 'NewData', 
                                                                                                            the_first_is_the_last,
                                                                                                            config)
            if isTraceLog:
                GroupBettingDataAccess.insert_association_by_AI((df_byAISPU,config))
            GroupBettingDataAccess.insert_association_suspicious_info((df_resultinfo,config))
            if config.transfer_score:
                GroupBettingDataAccess.insert_association_by_AI_to_CTS((df_byAI, date_insert, config))
            CommonDataAccess.update_association_stats_staging_status((BATCH,BATCH))
        if len(df)>len(IsNewdf):
            df['TJC'] = df.apply(lambda z: count_joining_combs(z['C1'], z['C2'],daily_cus_dict), axis=1)
            df_byAI,df_byAISPU,isTraceLog = Aggregate.transform_dataframe_to_support_aggregate(df, 'OnTheFly', the_first_is_the_last, config)
            if isTraceLog:
                GroupBettingDataAccess.insert_association_by_AI((df_byAISPU,config))
            if config.transfer_score:
                GroupBettingDataAccess.insert_association_by_AI_to_CTS((df_byAI, date_insert, config))
    
    def aggregate_when_day_end(args):
        """
        >>> Input   :   MinCustID               : integer
                        MaxCustID               : integer
                        date_insert             : string | format : YYYY-MM-DD
                        daily_cus_dict          : dictionary
                        the_first_is_the_last   : boolean
        """
        min_cus, max_cus, date_insert, daily_cus_dict, the_first_is_the_last, config = args
        try:
            try:
                df = GroupBettingDataAccess.get_association_stats((min_cus, max_cus, config))

                df['TJC'] = df.apply(lambda z: count_joining_combs(z['C1'], z['C2'], daily_cus_dict), axis=1)
                
                BuchOfDataFrames = Aggregate.transform_dataframe_to_support_aggregate(df, 'DayEnd', the_first_is_the_last, config)

                if the_first_is_the_last:
                    df_result3, df_resultinfo, df_byAI, df_byAISPU, isTraceLog = BuchOfDataFrames
                else:
                    df_result3,df_byAI,df_byAISPU,isTraceLog = BuchOfDataFrames
                # move to dba
                
                if isTraceLog:
                    GroupBettingDataAccess.insert_association_by_AI((df_byAISPU,config))
                        
                if the_first_is_the_last:
                    GroupBettingDataAccess.insert_association_suspicious_info((df_resultinfo,config))


            except Exception as err:
                # logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
                print(f'{config.ENV} | Day-end function | Error insert_association_by_AI and insert_association_suspicious_info: {err}')
                # message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError

            # insert dba CTS
            if config.transfer_score:
                try:
                    GroupBettingDataAccess.insert_association_by_AI_to_CTS((df_byAI, date_insert, config))

                except Exception as err:
                    # logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                    print(f'{config.ENV} | Error insert table byAI in DBA CTS: {err}')
                    # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                    # SendLogTelegram.send_message(message_telegram)
                    raise ValueError
                
            # Compute accomulatedly
            df_sampleDailyScore = df[['sample_id', 'C1',
                                    'C2', 'AccTS', 'AccMS', 'AccLS', 'AccTJD', 'AccTJSC']]
            df_DailyScore = df_sampleDailyScore.groupby('sample_id').first()

            
            # print('df_result3',df_result3.head(),sep='\n')
            # df_result3.set_index('sample_id',inplace=True)
            df_DailyScore = pd.merge(df_DailyScore,df_result3[['TS','MS','LS','TJC','TJSC','BC']],left_index=True, right_index=True)
            # print('df_DailyScore',df_DailyScore.head(),sep='\n')
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

            # print()
            
            df_byAISample03 = df_DailyScore[['C1', 'C2', 'S','AccTJSC']]
            df_byAISample03.rename(columns={'AccTJSC':'TJSC'},inplace=True)
            df_byAI = df_byAISample03[(df_byAISample03['S'] >= config.percent_score) & (
                df_byAISample03['TJSC'] >= config.combination_threshold)]
                    
            isTraceLog = False
            df_byAISPU = pd.DataFrame()
            if len(df_byAI.index) != 0:
                isTraceLog = True
                df_result4 = df_DailyScore[['TS', 'MS', 'LS', 'TJD', 'TJC']]
                df_byAISPU = pd.merge(df_result4, df_byAI,
                                    left_index=True, right_index=True)

            try:
                if isTraceLog:
                    GroupBettingDataAccess.insert_association_by_AI((df_byAISPU,config))

                GroupBettingDataAccess.insert_association_stats((df_DailyScore, date_insert, config))

            except Exception as err:
                # logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
                print(f'{config.ENV} | Day-end function | Error insert_association_by_AI or insert_association_stats: {err}')
                # message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError

            # insert dba CTS
            if config.transfer_score:
                try:
                    GroupBettingDataAccess.insert_association_by_AI_to_CTS((df_byAI, date_insert, config))

                except Exception as err:
                    # logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                    print(f'{config.ENV} | Error insert table byAI in DBA CTS: {err}')
                    # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                    # SendLogTelegram.send_message(message_telegram)
                    raise ValueError
        except Exception as err:
            # logging.error(f'{ENV} | Error in day-end agg function: {err}')
            print(f'{config.ENV} | Error in day-end agg function: {err}')
            # message_telegram = f'{ENV} | Error in day-end agg function: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError
    