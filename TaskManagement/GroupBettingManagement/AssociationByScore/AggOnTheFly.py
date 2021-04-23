import sys

##PROD
# sys.path.append("/home/vnteam/app/")
##LOCAL
from DataAccess.GroupBettingDA.CTS_DataCenter.AssociationByAICTS import AssociationByAICTSDA
from DataAccess.GroupBettingDA.SPU_AIML.AssociationByAISPU import AssociationByAISPUDA
from DataAccess.GroupBettingDA.SPU_AIML.AssociationSuspiciousInfo import AssociationSuspiciousInfoDA

sys.path.append("D:\\Project\\aiml_cleancode\\")
from DataAccess.GroupBettingDA.SPU_AIML.AssociationStatsStaging import AssociationStatsStagingDA
from TaskManagement.GroupBettingManagement.AssociationByScore import FeatureScore
from Configuration.Configuration import config
#from GroupBetting.Support import helper
from Utilities import FunctionSupport
import time
import os
import pandas as pd
import logging


def aggregate(args):
    try:
        date_insert = args[1]
        daily_cus_dict = args[2]
        time_getStaging = time.time()
        association_by_aicts_da = AssociationByAICTSDA()
        association_by_aispu_da = AssociationByAISPUDA()
        association_stats_staging_da = AssociationStatsStagingDA()
        association_suspicious_info_da = AssociationSuspiciousInfoDA()

        dba_results = association_stats_staging_da.get(args[0])
        
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
            
            df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = FeatureScore.calculate_score(IsNewdf,config,True)
            
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
                association_by_aispu_da.insert(chunks5)
            association_suspicious_info_da.insert(chunks2)
            
            # insert dba CTS
            if config.transfer_score:
                association_by_aicts_da.insert(chunks4, date_insert)

            # update Staging Status
            association_stats_staging_da.update(args[0])

            #logging.info(f"Time to insert all table in DB: {time.time() - time_inserttable}")
        if len(df)>len(IsNewdf):
            time_onthefly = time.time()
            df['TJC']=df.apply(lambda z : FunctionSupport.count_joining_combs_by_daily_cus_dict(z['C1'],z['C2'],daily_cus_dict),axis=1)
            df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
            df = df.astype({"sample_id": 'int64'})
            df['TS'] = df['TS'].astype('float')
            
            df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = FeatureScore.calculate_score(df,config)
            
            # move to dba
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")

            chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]

            if isTraceLog:
                association_by_aispu_da.insert(chunks5)
            # insert dba CTS
            if config.transfer_score:
                association_by_aicts_da.insert(chunks4, date_insert)
        logging.info(f"Time to complete child process {os.getpid()}: {time.time() - time_getStaging}")
    except Exception as err:
        message_telegram = f'{config.ENV} | Error in agg function: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError
