import logging
import os
import sys
import time

import pandas as pd

sys.path.append("D:\\working\\aiml\\")
from Configuration.Configuration import config
from DataAccess.GroupBettingDA.CTS_DataCenter.AssociationByAICTS import AssociationByAICTSDA
from DataAccess.GroupBettingDA.SPU_AIML.AssociationByAISPU import AssociationByAISPUDA
from DataAccess.GroupBettingDA.SPU_AIML.AssociationStats import AssociationStatsDA
from DataAccess.GroupBettingDA.SPU_AIML.AssociationSuspiciousInfo import AssociationSuspiciousInfoDA
from GroupBettingController.AssociationByScore import FeatureScore
from Utilities import FunctionSupport

##PROD
# sys.path.append("/home/vnteam/app/")
##LOCAL


def day_end_aggregate(args):
    try:
        date_insert = args[2]
        the_first_is_the_last = args[3]
        daily_cus_dict = args[4]
        time_getStaging = time.time()
        agg_day_end_controller = AggDayEndController()

        df = agg_day_end_controller.get_association_stats_df(args)
        df = agg_day_end_controller.fill_0_to_nan(df)
        df = agg_day_end_controller.preprocess_df(df, daily_cus_dict)

        df_byAI, df_byAISPU, df_resultinfo, isTraceLog, df_result3 = FeatureScore.calculate_score(df, config, the_first_is_the_last, True)

        agg_day_end_controller.save_phase2_to_dba(df_byAI, df_byAISPU, df_resultinfo, isTraceLog, the_first_is_the_last, date_insert)

        df_DailyScore = agg_day_end_controller.get_df_dailyscore(df, df_result3)

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

        agg_day_end_controller.save_aggregate_to_dba(df_DailyScore, df_byAI, df_byAISPU, isTraceLog, date_insert)
        logging.info(f"Time to complete child process into phase Acc day-end {os.getpid()}: {time.time() - time_getStaging}")

    except Exception as err:
        message_telegram = f'{config.ENV} | Error in day-end agg function: {err}'
        # FunctionSupport.notify_logging(message_telegram)
        print(message_telegram)
        raise ValueError


class AggDayEndController:
    def __init__(self):
        self.association_by_aicts_da = AssociationByAICTSDA()
        self.association_by_aispu_da = AssociationByAISPUDA()
        self.association_stats_da = AssociationStatsDA()
        self.association_suspicious_info_da = AssociationSuspiciousInfoDA()

    def get_association_stats_df(self, args):
        dba_results = self.association_stats_da.get(int(args[0]), int(args[1]))

        if len(dba_results[0]) == 0:
            return True
        df = pd.DataFrame(dba_results[0], columns=[
            "C1"
            , "C2"
            , "TS"
            , "ML"
            , "BL"
            , "LeagueID"
            , "IsMajorLeague"
            , "TJC"
            , "IsNew"
            , "AccTS"
            , "AccMS"
            , "AccLS"
            , "AccTJD"
            , "AccTJSC"
        ])
        return df

    def fill_0_to_nan(self, df):
        df['AccTS'].fillna(0, inplace=True)
        df['AccMS'].fillna(0, inplace=True)
        df['AccLS'].fillna(0, inplace=True)
        df['AccTJD'].fillna(0, inplace=True)
        df['AccTJSC'].fillna(0, inplace=True)
        return df

    def preprocess_df(self, df, daily_cus_dict):
        df['TJC'] = df.apply(
            lambda z: FunctionSupport.count_joining_combs_by_daily_cus_dict(z['C1'], z['C2'], daily_cus_dict), axis=1)

        df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)

        df = df.astype({"sample_id": 'int64'})
        df['TS'] = df['TS'].astype('float')
        df['AccTS'] = df['AccTS'].astype('float')
        df['AccMS'] = df['AccMS'].astype('float')
        df['AccLS'] = df['AccLS'].astype('float')
        return df

    def save_phase2_to_dba(self, df_byAI, df_byAISPU, df_resultinfo, isTraceLog, the_first_is_the_last, date_insert):
        # move to dba
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")
        fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")
        fulldatainfo_dba = df_resultinfo.to_dict(orient="records")

        chunks2 = [fulldatainfo_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatainfo_dba), config.chunk_size)]
        chunks4 = [fulldatabyAI_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]

        if isTraceLog:
            self.association_by_aispu_da.insert(chunks5)
        if the_first_is_the_last:
            self.association_suspicious_info_da.insert(chunks2)
        # insert dba CTS
        if config.transfer_score:
            self.association_by_aicts_da.insert(chunks4, date_insert)

    def get_df_dailyscore(self, df, df_result3):
        # Compute accomulatedly
        df_sampleDailyScore = df[['sample_id', 'C1',
                                  'C2', 'AccTS', 'AccMS', 'AccLS', 'AccTJD', 'AccTJSC']]

        df_DailyScore = df_sampleDailyScore.groupby('sample_id').first()
        df_DailyScore = pd.merge(df_DailyScore, df_result3[['TS','MS','LS','TJC','TJSC','BC']],left_index=True, right_index=True)
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
        return df_DailyScore

    def save_aggregate_to_dba(self, df_DailyScore, df_byAI, df_byAISPU, isTraceLog, date_insert):
        # move to dba
        fulldata_dba = df_DailyScore.to_dict(orient="records")
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")
        fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")

        chunks1 = [fulldata_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldata_dba), config.chunk_size)]

        chunks4 = [fulldatabyAI_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x + config.chunk_size]
                   for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]

        if isTraceLog:
            self.association_by_aispu_da.insert(chunks5)

        self.association_stats_da.insert(chunks1, date_insert)

        if config.transfer_score:
            self.association_by_aicts_da.insert(chunks4, date_insert)
