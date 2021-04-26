import sys

##PROD
# sys.path.append("/home/vnteam/app/")
##LOCAL
from DataAccess.GroupBettingDA.CTS_DataCenter.AssociationByAICTS import AssociationByAICTSDA
from DataAccess.GroupBettingDA.SPU_AIML.AssociationByAISPU import AssociationByAISPUDA
from DataAccess.GroupBettingDA.SPU_AIML.AssociationSuspiciousInfo import AssociationSuspiciousInfoDA

sys.path.append("D:\\Project\\aiml_cleancode\\")
from DataAccess.GroupBettingDA.SPU_AIML.AssociationStats import AssociationStatsDA
from GroupBettingController.AssociationByScore import FeatureScore
from Configuration.Configuration import config
from Utilities import FunctionSupport
import time
import os
import pandas as pd
import logging


def day_end_aggregate(args):
    try:
        date_insert = args[2]
        the_first_is_the_last = args[3]
        daily_cus_dict = args[4]
        time_getStaging = time.time()
        association_by_aicts_da = AssociationByAICTSDA()
        association_by_aispu_da = AssociationByAISPUDA()
        association_stats_da = AssociationStatsDA()
        association_suspicious_info_da = AssociationSuspiciousInfoDA()

        dba_results = association_stats_da.get(int(args[0]), int(args[1]))

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

        df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = FeatureScore.calculate_score(df, config, the_first_is_the_last, True)
        
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
            association_by_aispu_da.insert(chunks5)
        if the_first_is_the_last:
            association_suspicious_info_da.insert(chunks2)
        # insert dba CTS
        if config.transfer_score:
            association_by_aicts_da.insert(chunks4, date_insert)
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

        df_DailyScore.rename(columns={'AccTS': 'TS', 'AccMS': 'MS', 'AccLS': 'LS', 'AccTJD': 'TJD'},inplace=True)

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
            association_by_aispu_da.insert(chunks5)
            
        association_stats_da.insert(chunks1, date_insert)

        if config.transfer_score:
            association_by_aicts_da.insert(chunks4, date_insert)
    
        logging.info(f"Time to complete child process into phase Acc day-end {os.getpid()}: {time.time() - time_getStaging}")
    except Exception as err:
        message_telegram = f'{config.ENV} | Error in day-end agg function: {err}'
        # FunctionSupport.notify_logging(message_telegram)
        print(message_telegram)
        raise ValueError
