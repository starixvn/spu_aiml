from DataAccess.Model.SPU_AIML.SPU_TruncateTableDAModel import SPU_TruncateTableDAModel
import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import os
import json
import pickle
import numpy as np
import time
import logging
import multiprocessing as mp
import pandas as pd
from tqdm import tqdm
from Configuration.Configuration import config
from DataAccess.Model.SPU_AIML.SPU_UpdateScanStatusDAModel import SPU_UpdateScanStatusDAModel
from DataAccess.Model.SPU_AIML.SPU_GetAssociationStatsDAModel import SPU_GetAssociationStatsDAModel
from DataAccess.Model.SPU_AIML.SPU_GetAssociationStatsStagingDAModel import SPU_GetAssociationStatsStagingDAModel
from DataAccess.Model.SPU_AIML.SPU_InsertAssociationByAIDAModel import SPU_InsertAssociationByAIDAModel
from DataAccess.Model.SPU_AIML.SPU_InsertAssociationStatsDAModel import SPU_InsertAssociationStatsDAModel
from DataAccess.Model.SPU_AIML.SPU_InsertAssociationStatsStagingDAModel import SPU_InsertAssociationStatsStagingDAModel
from DataAccess.Model.SPU_AIML.SPU_InsertAssociationSuspiciousInfoDAModel import SPU_InsertAssociationSuspiciousInfoDAModel
from DataAccess.Model.SPU_AIML.SPU_UpdateAssociationStatsStagingStatusDAModel import SPU_UpdateAssociationStatsStagingStatusDAModel
from DataAccess.Model.CTS_DataCenter.CTS_InsertAssociationByAIDAModel import CTS_InsertAssociationByAIDAModel
from DataAccess.DataAccessConnection import DataAccessConnection
from DataAccess.DataAccessConnection import spu_aiml,cts_datacenter
from DataAccess.CoreDA.BaseDA import BaseDA
from Utilities import Utilities


class ComputeGroupBetting(object):
    def __init__(self,*args):
        self.data_env = args[0]
        self.batch_cus_list = args[1]
        self.daily_cus_dict = args[2]
        self.date_insert = args[3]
        self.time_start = args[4]
        
    def run(self):
        time_start = time.time()
        try:
            time_constant = self.check_day_end()
            if time_constant !=0 :
                start_time = time.time()
                the_first_is_the_last = False
                if len(self.data_env.initial)>2:
                    print("Tinh new batch voi day end")
                    self.compute_GroupBetting_new_batch()
                else:
                    the_first_is_the_last = True
                self.date_insert=self.data_env.year_prev+'-'+self.data_env.month_prev+'-'+self.data_env.day_prev
                print(f'{config.ENV} | date_insert when DAY END {self.date_insert}')
                self.compute_GroupBetting_accumulate_batch(the_first_is_the_last)
                
                connection_spu = DataAccessConnection(spu_aiml)
                ip_param = SPU_UpdateScanStatusDAModel(self.date_insert)
                BaseDA.execute("SPU_AIML_UpdateScanStatus",spu_aiml,ip_param,connection_spu)
                print("***********************************************************************************************************************************************************************************")
                print("%s | AGG & INSERT TIME %.0f SECONDS" %
                    (config.ENV,time.time() - start_time))
                # message_telegram = f"{config.ENV} | Group Betting is done, total {round((time.time() - time_begin)/3600,4)} hours "
                # Utilities.notify_logging(message_telegram,True)
                ip_param = SPU_TruncateTableDAModel("AssociationStatsStaging")
                BaseDA.execute("SPU_AIML_DBA_Truncate_Table",spu_aiml,ip_param,connection_spu)
                
                check_cus_files=os.listdir(config.root)
                
                if config.cus_list_fn in check_cus_files:
                    os.remove(os.path.join(config.root,config.cus_list_fn))
                    
                if config.cus_dict_fn in check_cus_files:
                    os.remove(os.path.join(config.root,config.cus_dict_fn))
                del connection_spu
                self.data_env.initial.clear()
                #continue
                return True
            print("tinh new batch khong dayend")
            self.compute_GroupBetting_new_batch()
            logging.info(f'{config.app_name} | {config.ENV} | INFO | ComputeGroupBetting was completed in {time.time() - time_start} seconds ({round((time.time() - time_start)/3600,4)} hours)')
        except Exception as e:
            message_telegram = f"function ComputeGroupBetting | {e}"
            raise ValueError(message_telegram)  

    def data_suspiciousInfo(self,df):
        susinfo = df[['sample_id', 'ML', 'BL']]
        df_susinfo = Utilities.transform_to_list(susinfo)
        df_susinfo = df_susinfo.set_index('sample_id')
        df_susinfo['ML'] = [','.join(map(str, l)) for l in df_susinfo['ML']]
        df_susinfo['BL'] = [','.join(map(str, l)) for l in df_susinfo['BL']]
        return df_susinfo
    
    def compute_GroupBetting_new_batch(self):
        try:
            start_time = time.time()
            # build batches
            batch_cus_list = sorted(self.batch_cus_list)
            BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+config.num_batch_cus]]) for x in range(0, len(batch_cus_list), config.num_batch_cus)]
            logging.info(f"number of cust list: {len(batch_cus_list)}")
            pool = mp.Pool(config.nb_workers_phase_2)
            for _ in tqdm(pool.imap_unordered(self.aggregate_on_the_fly,BATCHES),total=len(BATCHES),desc=f'AGG | A BATCH OF {self.date_insert}'):
                pass
            pool.close()
            pool.join()
            logging.info(f'A BATCH of {self.date_insert} done in {time.time()-start_time} seconds')
        except Exception as e:
            message_telegram = f"function compute_GroupBetting_new_batch | {e}"
            raise ValueError(message_telegram)  
        
    def compute_GroupBetting_accumulate_batch(self,the_first_is_the_last):
        try:
            daily_cus_list = Utilities.load_a_file(config.root, config.cus_list_fn)
            daily_cus_dict = Utilities.load_a_file(config.root, config.cus_dict_fn)
            daily_cus_list = np.sort(daily_cus_list)
            
            BATCHES = [daily_cus_list[x:x+config.num_batch_cus] for x in range(0, len(daily_cus_list), config.num_batch_cus)]
            pool = mp.Pool(config.nb_workers_phase_2)
            for _ in tqdm(pool.imap_unordered(self.aggregate_day_end,[(min(BATCH),max(BATCH),the_first_is_the_last) for BATCH in BATCHES]), total=len(BATCHES), desc='DAY-END AGG'):
                pass
            pool.close()
            pool.join()
        except Exception as e:
            message_telegram = f"function compute_GroupBetting_accumulate_batch | {e}"
            raise ValueError(message_telegram)
        
    def check_day_end(self):
        try:
            check_files = [f for f in sorted(os.listdir(config.root_orig))]
            while len(check_files)==0:
                time.sleep(config.time_sleep)
                check_files = [f for f in sorted(os.listdir(config.root_orig))]
            orig_fn = check_files[0]
            day_curr=orig_fn.split('.')[0].split('_')[2]
            self.data_env.initial.append(day_curr)
            time_constant=int(day_curr)-int(self.data_env.day_prev)
            return time_constant
        except Exception as e:
            message_telegram = f"function check_day_end | {e}"
            raise ValueError(message_telegram)
            
    def aggregate_on_the_fly(self,args):
        try:
            time_getStaging = time.time()
            
            connection_spu = DataAccessConnection(spu_aiml)
            connection_cts = DataAccessConnection(cts_datacenter)
            
            ip_param = SPU_GetAssociationStatsStagingDAModel(args)
            dba_results = BaseDA.execute("SPU_AIML_GetAssociationStatsStaging", spu_aiml, ip_param, connection_spu)
            
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
                time_newBatch = time.time()
                IsNewdf['sample_id'] = IsNewdf['C1'].map(str) + IsNewdf['C2'].map(str)
                IsNewdf = IsNewdf.astype({"sample_id": 'int64'})
                IsNewdf['TS'] = IsNewdf['TS'].astype('float')
                
                df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = self.calculate_score(IsNewdf,config,True)
                
                # move to dba
                fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
                fulldatabyAI_dba = df_byAI.to_dict(orient="records")
                fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")


                chunks2 = [fulldatainfo_dba[x:x+config.chunk_size]
                        for x in range(0, len(fulldatainfo_dba), config.chunk_size)]


                chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                        for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

                chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                        for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]
                #logging.info(f"Time to calculate new batch: {time.time() - time_newBatch}")
                time_inserttable = time.time()
                if isTraceLog:
                    for chunk in chunks5:
                        chunk = json.dumps(chunk)
                        ip_param = SPU_InsertAssociationByAIDAModel(chunk)
                        BaseDA.execute("SPU_AIML_InsertAssociationByAI",spu_aiml,ip_param,connection_spu)
                for chunk in chunks2:
                    chunk = json.dumps(chunk)
                    ip_param = SPU_InsertAssociationSuspiciousInfoDAModel(chunk)
                    BaseDA.execute("SPU_AIML_InsertAssociationSuspiciousInfo",spu_aiml,ip_param,connection_spu)
                
                # insert dba CTS
                if config.transfer_score:
                    for chunk in chunks4:
                        chunk = json.dumps(chunk)
                        ip_param = CTS_InsertAssociationByAIDAModel(chunk,self.date_insert)
                        BaseDA.execute("CTS_DC_Association_InsertAssociationByAI",cts_datacenter,ip_param,connection_cts)

                # update Staging Status
                ip_param = SPU_UpdateAssociationStatsStagingStatusDAModel(args[0])
                BaseDA.execute("SPU_AIML_UpdateAssociationStatsStagingStatus",spu_aiml,ip_param,connection_spu)
            if len(df)>len(IsNewdf):
                time_onthefly = time.time()
                df['TJC']=df.apply(lambda z : Utilities.count_joining_combs_by_daily_cus_dict(z['C1'],z['C2'],self.daily_cus_dict),axis=1)
                df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
                df = df.astype({"sample_id": 'int64'})
                df['TS'] = df['TS'].astype('float')
                
                df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = self.calculate_score(df,config)
                
                # move to dba
                fulldatabyAI_dba = df_byAI.to_dict(orient="records")
                fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")

                chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                        for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

                chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                        for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]

                if isTraceLog:
                    for chunk in chunks5:
                        chunk = json.dumps(chunk)
                        ip_param = SPU_InsertAssociationByAIDAModel(chunk)
                        BaseDA.execute("SPU_AIML_InsertAssociationByAI",spu_aiml,ip_param,connection_spu)
                # insert dba CTS
                if config.transfer_score:
                    for chunk in chunks4:
                        chunk = json.dumps(chunk)
                        ip_param = CTS_InsertAssociationByAIDAModel(chunk,self.date_insert)
                        BaseDA.execute("CTS_DC_Association_InsertAssociationByAI",cts_datacenter,ip_param,connection_cts)
            logging.info(f"Time to complete child process {os.getpid()}: {time.time() - time_getStaging}")
            del connection_spu, connection_cts
        except Exception as e:
            message_telegram = f"function aggregate_on_the_fly | {e}"
            raise ValueError(message_telegram)
        
    def leaguescore_dataflow(self,df):
        try:
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
                lambda x: Utilities.total_leaguescore(x['minor'], x['major']), axis=1)
            return df_leaguescore
        except Exception as e:
            message_telegram = f"function leaguescore_dataflow | {e}"
            raise ValueError(message_telegram)
        
    def calculate_score(self,df,config,isCreateSusInfo = False,isDayEnd = False):
        try:
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
        except Exception as e:
            message_telegram = f"function calculate_score | {e}"
            raise ValueError(message_telegram)
        
    def aggregate_day_end(self,args):
        try:
            connection_spu = DataAccessConnection(spu_aiml)
            connection_cts = DataAccessConnection(cts_datacenter)
            the_first_is_the_last = args[2]
            time_getStaging = time.time()
            ip_param = SPU_GetAssociationStatsDAModel(int(args[0]), int(args[1]))
            dba_results = BaseDA.execute("SPU_AIML_GetAssociationStats",spu_aiml,ip_param,connection_spu)
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
                lambda z: Utilities.count_joining_combs_by_daily_cus_dict(z['C1'], z['C2'],self.daily_cus_dict), axis=1)
            
            df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
            
            df = df.astype({"sample_id": 'int64'})
            df['TS'] = df['TS'].astype('float')
            df['AccTS'] = df['AccTS'].astype('float')
            df['AccMS'] = df['AccMS'].astype('float')
            df['AccLS'] = df['AccLS'].astype('float')

            df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = self.calculate_score(df,config,the_first_is_the_last,True)
            
            # move to dba
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")
            fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
            
            chunks2 = [fulldatainfo_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatainfo_dba), config.chunk_size)]
            chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]   
            
            if isTraceLog:
                for chunk in chunks5:
                    chunk = json.dumps(chunk)
                    ip_param = SPU_InsertAssociationByAIDAModel(chunk)
                    BaseDA.execute("SPU_AIML_InsertAssociationByAI",spu_aiml,ip_param,connection_spu)
            if the_first_is_the_last:
                for chunk in chunks2:
                    chunk = json.dumps(chunk)
                    ip_param = SPU_InsertAssociationByAIDAModel(chunk)
                    BaseDA.execute("SPU_AIML_InsertAssociationSuspiciousInfo",spu_aiml,ip_param,connection_spu)
            # insert dba CTS
            if config.transfer_score:
                for chunk in chunks4:
                    chunk = json.dumps(chunk)
                    ip_param = CTS_InsertAssociationByAIDAModel(chunk,self.date_insert)
                    BaseDA.execute("CTS_DC_Association_InsertAssociationByAI",cts_datacenter,ip_param,connection_cts)
            
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
            df_byAI = df_byAISample03[(df_byAISample03['S'] >= config.percent_score) & (
                df_byAISample03['TJSC'] >= config.combination_threshold)]
                    
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


            chunks1 = [fulldata_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldata_dba), config.chunk_size)]

            chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]  
            
            if isTraceLog:
                for chunk in chunks5:
                    chunk = json.dumps(chunk)
                    ip_param = SPU_InsertAssociationByAIDAModel(chunk)
                    BaseDA.execute("SPU_AIML_InsertAssociationByAI",spu_aiml,ip_param,connection_spu)
                
            for chunk in chunks1:
                chunk = json.dumps(chunk)
                ip_param = SPU_InsertAssociationStatsDAModel(chunk,self.date_insert)
                BaseDA.execute("SPU_AIML_InsertAssociationStats",spu_aiml,ip_param,connection_spu)

            if config.transfer_score:
                for chunk in chunks4:
                    chunk = json.dumps(chunk)
                    ip_param = CTS_InsertAssociationByAIDAModel(chunk,self.date_insert)
                    BaseDA.execute("CTS_DC_Association_InsertAssociationByAI",cts_datacenter,ip_param,connection_cts)
        
            logging.info(f"Time to complete child process into phase Acc day-end {os.getpid()}: {time.time() - time_getStaging}")
            del connection_cts,connection_spu
        except Exception as e:
            message_telegram = f"function aggregate_day_end | {e}"
            raise ValueError(message_telegram)