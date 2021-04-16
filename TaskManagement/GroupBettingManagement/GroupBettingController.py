import os
import time
from TaskManagement.GroupBettingManagement.AssociationByScore.AggScoreCouple import AggScoreCouple
from TaskManagement.GroupBettingManagement.AssociationByIP.GroupbyIP import GroupbyIP
from TaskManagement.GroupBettingManagement.AssociationByScore.ExtractInsightData import ExtractInsightData
from TaskManagement.GroupBettingManagement.AssociationByScore.PrepareDataEnv import PrepareDataEnv
from DataAccess.GroupBettingDA.SPU_AIML import AssociationStatsStaging
from app import config


class GroupBettingController(object):
    def clean_dataenv(self,config):
        AssociationStatsStaging.TruncateAssociationStatsStaging()
        check_cus_files=os.listdir(config.root)
        if config.cus_list_fn in check_cus_files:
            os.remove(os.path.join(config.root,config.cus_list_fn))
        if config.cus_dict_fn in check_cus_files:
            os.remove(os.path.join(config.root,config.cus_dict_fn))
            
    def run(self):
        self.clean_dataenv(config)
        initial = []
        while True:
            data_env = PrepareDataEnv(initial)
            df_dataip, date_insert,day_prev, batch_cus_dict, daily_cus_dict, isContinue = data_env.run()
            if isContinue:
                time.sleep(config.time_sleep)
                continue
            association_ip = GroupbyIP(df_dataip,date_insert)
            association_ip.run()
            calculate_data = ExtractInsightData(batch_cus_dict)
            calculate_data.run()
            agg_score = AggScoreCouple(data_env.initail, day_prev, batch_cus_dict, daily_cus_dict, date_insert)
            agg_score.run()