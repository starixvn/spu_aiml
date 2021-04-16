import pandas as pd
import numpy as np
from numba import prange, njit, set_num_threads, jit
from numba.typed import List
import numba
from tqdm import tqdm
from Utilities import FunctionSupport


class AlgorithmFeatureScore(object):
    def total_leaguescore(self,x, y):
        if y == 1:
            return (x + 5/2) * (2/7)
        elif x == 1:
            return (y + 3/2) * (2/5)
        elif y != 1 and x != 1:
            minor_score = (x + 5/2) * (2/7)
            major_score = (y + 3/2) * (2/5)
            return (3 * (minor_score + 1) + (major_score + 2)) * (1/9)

    def leaguescore_dataflow(self,df):
        # version 4
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
            lambda x: FunctionSupport.total_leaguescore(x['minor'], x['major']), axis=1)
        return df_leaguescore

    def data_suspiciousInfo(self,df):
        susinfo = df[['sample_id', 'ML', 'BL']]
        df_susinfo = FunctionSupport.transform_to_list(susinfo)
        df_susinfo = df_susinfo.set_index('sample_id')
        df_susinfo['ML'] = [','.join(map(str, l)) for l in df_susinfo['ML']]
        df_susinfo['BL'] = [','.join(map(str, l)) for l in df_susinfo['BL']]
        return df_susinfo

    def transform_to_list(self,df):
        keys, values1, values2 = df.sort_values('sample_id').values.T
        ukeys, index = np.unique(keys, True)
        arrays = np.split(values1, index[1:])
        arrays2 = np.split(values2, index[1:])
        df2 = pd.DataFrame({'sample_id': ukeys, 'ML': [list(
            a) for a in arrays], 'BL': [list(b) for b in arrays2]})
        return df2

    def calculate_score(self,df,config,isCreateSusInfo = False,isDayEnd = False):
        df_custid = pd.DataFrame()
        df_custid = df.groupby('sample_id')[['C1', 'C2', 'TJC']].first()

        # calculate League Score
        df_leaguescore = self.leaguescore_dataflow(df)
        
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
            df_susinfo = self.data_suspiciousInfo(df)
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
        df_result3['TJD'] = 1
        if len(df_byAI.index) != 0:
            isTraceLog = True
            df_result4 = df_result3[['TS', 'MS', 'LS', 'TJD', 'TJC']]
            df_byAISPU = pd.merge(df_result4, df_byAI,
                                left_index=True, right_index=True)
            
        return df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3

    @njit(parallel=True)
    def compute_pairwise_cus(self,X,time_threshold,n_jobs=4):
        set_num_threads(n_jobs)
        n = X.shape[0]
        mat = np.empty((n, n), np.float64)
        for i in prange(n-1):
            for j in range(i+1, n):
                mat[i, j] = mat[j, i] = self.calculate_difference(X[i], X[j], time_threshold)

        np.fill_diagonal(mat, 0.0)   
        return mat

    @njit
    def calculate_difference(self,ls1, ls2, time_threshold):
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
        zip_time = np.column_stack((time_arr[1:],time_arr[:-1]))
        eff_zip_time = zip_time[diff_cus != 0]
        diff_time=eff_zip_time[:,0]-eff_zip_time[:,1]
        eff_diff_time=diff_time[diff_time<=20]
        
        if len(eff_diff_time)==0:
            time_score = 0
        else:
            time_score = (time_threshold-np.mean(eff_diff_time)) / time_threshold
        return time_score