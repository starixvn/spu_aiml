import sys

##PROD
# sys.path.append("/home/vnteam/app/")
##LOCAL
from DataAccess.GroupBettingDA.AssociationByAICTS import AssociationByAICTSDA
from DataAccess.GroupBettingDA.AssociationByAISPU import AssociationByAISPUDA
from DataAccess.GroupBettingDA.AssociationSuspiciousInfo import AssociationSuspiciousInfoDA

sys.path.append("D:\\Project\\aiml_cleancode\\")
from DataAccess.GroupBettingDA.AssociationStatsStaging import AssociationStatsStagingDA
from Controller.AssociationByScore.GroupBettingExtraction import FeatureScore
from Configuration.Configuration import config
from Helper import Utilities
import time
import os
import pandas as pd
import logging


def aggregate(args):
    try:
        date_insert = args[1]
        daily_cus_dict = args[2]
        time_getStaging = time.time()
        agg_on_the_fly_controller = AggOnTheFlyController()

        df = agg_on_the_fly_controller.get_association_stats_staging_df(args)
        IsNewdf=df[df.IsNew==1]

        if not IsNewdf.empty:
            IsNewdf['sample_id'] = IsNewdf['C1'].map(str) + IsNewdf['C2'].map(str)
            IsNewdf = IsNewdf.astype({"sample_id": 'int64'})
            IsNewdf['TS'] = IsNewdf['TS'].astype('float')
            
            df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = FeatureScore.calculate_score(IsNewdf, config, True)

            agg_on_the_fly_controller.save_batch_to_dba(df_resultinfo, df_byAI, df_byAISPU, isTraceLog, args)

        if len(df)>len(IsNewdf):
            df['TJC']=df.apply(lambda z : Utilities.count_joining_combs_by_daily_cus_dict(z['C1'],z['C2'],daily_cus_dict),axis=1)
            df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
            df = df.astype({"sample_id": 'int64'})
            df['TS'] = df['TS'].astype('float')
            
            df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = FeatureScore.calculate_score(df, config)

            agg_on_the_fly_controller.save_full_to_dba(df_byAI, df_byAISPU, isTraceLog, date_insert)

        logging.info(f"Time to complete child process {os.getpid()}: {time.time() - time_getStaging}")
    except Exception as err:
        message_telegram = f'GROUP BETTING | {config.ENV} | Error in on-the-fly agg function: {err}'
        Utilities.notify_logging(message_telegram)
        raise ValueError


class AggOnTheFlyController:

    def __init__(self):
        self.association_by_aicts_da = AssociationByAICTSDA()
        self.association_by_aispu_da = AssociationByAISPUDA()
        self.association_stats_staging_da = AssociationStatsStagingDA()
        self.association_suspicious_info_da = AssociationSuspiciousInfoDA()

    def get_association_stats_staging_df(self, args):
        dba_results = self.association_stats_staging_da.get(args[0])

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
        return df

    def save_batch_to_dba(self, df_resultinfo, df_byAI, df_byAISPU, isTraceLog, args):
        fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")
        fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")
        date_insert = args[1]

        chunks2 = [fulldatainfo_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatainfo_dba), config.chunk_size)]

        chunks4 = [fulldatabyAI_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]
        if isTraceLog:
            self.association_by_aispu_da.insert(chunks5)
        self.association_suspicious_info_da.insert(chunks2)

        # insert dba CTS
        if config.transfer_score:
            self.association_by_aicts_da.insert(chunks4, date_insert)

        # update Staging Status
        self.association_stats_staging_da.update(args[0])

    def save_full_to_dba(self, df_byAI, df_byAISPU, isTraceLog, date_insert):
        # move to dba
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")
        fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")

        chunks4 = [fulldatabyAI_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]

        if isTraceLog:
            self.association_by_aispu_da.insert(chunks5)

        if config.transfer_score:
            self.association_by_aicts_da.insert(chunks4, date_insert)
