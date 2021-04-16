import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import os
import pickle
import numpy as np
import time
import logging
import multiprocessing as mp
import pandas as pd
from tqdm import tqdm
from TaskManagement.GroupBettingManagement.GroupBettingController import config
from DataAccess.CommonDA import SystemParameter
from DataAccess.GroupBettingDA.SPU_AIML import AssociationByAISPU
from DataAccess.GroupBettingDA.SPU_AIML import AssociationStats
from DataAccess.GroupBettingDA.SPU_AIML import AssociationStatsStaging
from DataAccess.GroupBettingDA.SPU_AIML import AssociationSuspiciousInfo
from DataAccess.GroupBettingDA.CTS_DataCenter import AssociationByAICTS
from TaskManagement.GroupBettingManagement.AssociationByScore.AlgorithmFeatureScore import AlgorithmFeatureScore
from Utilities import FunctionSupport



class AggScoreCouple(object):
    def __init__(self,*args):
        self.initail = args[0]
        self.day_prev = args[1]
        self.batch_cus_list = args[2]
        self.daily_cus_dict = args[3]
        self.date_insert = args[4]
        
    def count_joining_combs_by_daily_cus_dict(cus1,cus2,daily_cus_dict):
        """
        >>> Input   : cus1,cus2
        >>> Output  : number of joining combinations
        """
        comb_a, comb_b = set(daily_cus_dict[cus1]), set(daily_cus_dict[cus2])
        return len(comb_a.intersection(comb_b))
        
    def calculate_new_batch(self):
        try:
            start_time = time.time()
            # build batches
            batch_cus_list = sorted(self.batch_cus_list)
            BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+config.num_batch_cus]]) for x in range(0, len(batch_cus_list), config.num_batch_cus)]
            logging.info(f"number of cust list: {len(batch_cus_list)}")
            pool = mp.Pool(config.nb_workers_phase_2)
            for _ in tqdm(pool.imap_unordered(self.aggregate_on_the_fly(),[(BATCH,self.date_insert,self.daily_cus_dict) for BATCH in BATCHES]),total=len(BATCHES),desc=f'AGG | A BATCH OF {self.date_insert}'):
                pass
            pool.close()
            pool.join()
            logging.info(f'A BATCH of {self.date_insert} done in {time.time()-start_time} seconds')
        except Exception as e:
            message_telegram = f"{config.ENV} | Error phase 2 right before day end: {e}"
            FunctionSupport.notify_logging(message_telegram)
            return True
        
    def calculate_acc_batch(self,the_first_is_the_last):
        with open(os.path.join(config.root, config.cus_list_fn), 'rb') as f:
            daily_cus_list = pickle.load(f)
        with open(os.path.join(config.root, config.cus_dict_fn), 'rb') as g:
            daily_cus_dict = pickle.load(g)
        daily_cus_list = np.sort(daily_cus_list)
        BATCHES = [daily_cus_list[x:x+config.num_batch_cus] for x in range(0, len(daily_cus_list), config.num_batch_cus)]
        pool = mp.Pool(config.nb_workers_phase_2)
        for _ in tqdm(pool.imap_unordered(self.aggregate_day_end(),[(min(BATCH),max(BATCH),self.date_insert,the_first_is_the_last,daily_cus_dict) for BATCH in BATCHES]), total=len(BATCHES), desc='DAY-END AGG'):
            pass
        pool.close()
        pool.join()
        
    def check_day_end(self):
        time_begin = time.time()
        check_files = [f for f in sorted(os.listdir(config.root_orig))]
        while len(check_files)==0:
            time.sleep(config.time_sleep)
            check_files = [f for f in sorted(os.listdir(config.root_orig))]
        orig_fn = check_files[0]
        day_curr=orig_fn.split('.')[0].split('_')[2]
        self.initial.append(day_curr)
        time_constant=int(day_curr)-int(self.day_prev)
        return time_constant
    
    def run(self):
        time_constant = self.check_day_end()
        if time_constant !=0 :
            start_time = time.time()
            the_first_is_the_last = False
            if len(self.initial)>2:
                self.calculate_new_batch()
            else:
                the_first_is_the_last = True
            #date_insert=year_prev+'-'+month_prev+'-'+day_prev
            print(f'{config.ENV} | date_insert when DAY END {self.date_insert}')
            self.calculate_acc_batch(the_first_is_the_last)
            SystemParameter.InsertSystemParameter(self.date_insert)
            print("***********************************************************************************************************************************************************************************")
            print("%s | AGG & INSERT TIME %.0f SECONDS" %
                (config.ENV,time.time() - start_time))
            message_telegram = f"{config.ENV} | Group Betting is done, total {round((time.time() - time_begin)/3600,4)} hours "
            FunctionSupport.notify_logging(message_telegram,True)
            
            AssociationStatsStaging.TruncateAssociationStatsStaging()
            
            check_cus_files=os.listdir(config.root)
            if config.cus_list_fn in check_cus_files:
                os.remove(os.path.join(config.root,config.cus_list_fn))
            if config.cus_dict_fn in check_cus_files:
                os.remove(os.path.join(config.root,config.cus_dict_fn))
            initial = []
            #continue
            return True
                   
        self.calculate_new_batch()
            
    def aggregate_on_the_fly(self,args):
        try:
            date_insert = args[1]
            daily_cus_dict = args[2]
            time_getStaging = time.time()
            
            dba_results = AssociationStatsStaging.GetAssociationStatsStaging(args[0])
            
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
                
                df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = AlgorithmFeatureScore.calculate_score(IsNewdf,config,True)
                
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
                    AssociationByAISPU.InsertAssociationByAISPU(chunks5)
                AssociationSuspiciousInfo.InsertAssociationSuspiciousInfo(chunks2)
                
                # insert dba CTS
                if config.transfer_score:
                    AssociationByAICTS.InsertAssociationByAICTS(chunks4,date_insert)

                # update Staging Status
                AssociationStatsStaging.UpdateAssociationStatsStagingStatus(args[0])
            if len(df)>len(IsNewdf):
                time_onthefly = time.time()
                df['TJC']=df.apply(lambda z : FunctionSupport.count_joining_combs_by_daily_cus_dict(z['C1'],z['C2'],daily_cus_dict),axis=1)
                df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
                df = df.astype({"sample_id": 'int64'})
                df['TS'] = df['TS'].astype('float')
                
                df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = AlgorithmFeatureScore.calculate_score(df,config)
                
                # move to dba
                fulldatabyAI_dba = df_byAI.to_dict(orient="records")
                fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")

                chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                        for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

                chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                        for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]

                if isTraceLog:
                    AssociationByAISPU.InsertAssociationByAISPU(chunks5)
                # insert dba CTS
                if config.transfer_score:
                    AssociationByAICTS.InsertAssociationByAICTS(chunks4,date_insert)
            logging.info(f"Time to complete child process {os.getpid()}: {time.time() - time_getStaging}")
        except Exception as err:
            message_telegram = f'{config.ENV} | Error in agg function: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError
        
    def aggregate_day_end(self,args):
        try:
            date_insert = args[2]
            the_first_is_the_last = args[3]
            daily_cus_dict = args[4]
            time_getStaging = time.time()
        
            dba_results = AssociationStats.GetAssociationStats(int(args[0]), int(args[1]))
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
                lambda z: FunctionSupport.count_joining_combs_by_daily_cus_dict(z['C1'], z['C2'],daily_cus_dict), axis=1)
            
            df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
            
            df = df.astype({"sample_id": 'int64'})
            df['TS'] = df['TS'].astype('float')
            df['AccTS'] = df['AccTS'].astype('float')
            df['AccMS'] = df['AccMS'].astype('float')
            df['AccLS'] = df['AccLS'].astype('float')

            df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = AlgorithmFeatureScore.calculate_score(df,config,the_first_is_the_last,True)
            
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
                AssociationByAISPU.InsertAssociationByAISPU(chunks5)
            if the_first_is_the_last:
                AssociationSuspiciousInfo.InsertAssociationSuspiciousInfo(chunks2)
            # insert dba CTS
            if config.transfer_score:
                AssociationByAICTS.InsertAssociationByAICTS(chunks4,date_insert)
            
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
                AssociationByAISPU.InsertAssociationByAISPU(chunks5)
                
            AssociationStats.InsertAssociationStats(chunks1,date_insert)

            if config.transfer_score:
                AssociationByAICTS.InsertAssociationByAICTS(chunks4,date_insert)
        
            logging.info(f"Time to complete child process into phase Acc day-end {os.getpid()}: {time.time() - time_getStaging}")
        except Exception as err:
            message_telegram = f'{config.ENV} | Error in day-end agg function: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError