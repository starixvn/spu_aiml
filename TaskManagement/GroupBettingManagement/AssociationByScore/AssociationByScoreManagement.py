from Utilities.MultiException import ContinueGroupBetting
from Utilities import Utilities
from TaskManagement.GroupBettingManagement.AssociationByScore.ComputeGroupBetting import ComputeGroupBetting
from TaskManagement.GroupBettingManagement.AssociationByScore.BuildDataModel import BuildDataModel
#from test import testmultiprocess
from Configuration.Configuration import config


class AssociationByScoreManagement(object):
    def __init__(self,*args):
        self.data_env = args[0]
        self.batch_cus_dict = args[1]
        self.batch_cus_list = args[2]
        self.daily_cus_dict = args[3]
        self.date_insert = args[4]
        
    def run(self):
        try:
            calculate_data = BuildDataModel(self.batch_cus_dict)
            calculate_data.run()
            
            agg_score = ComputeGroupBetting(self.data_env, self.batch_cus_list, self.daily_cus_dict, self.date_insert)
            agg_score.run()
            return self.data_env.month_prev,self.data_env.day_prev,self.data_env.year_prev
        except Exception as e:
            message_telegram = f"{config.app_name} | {config.ENV} | Error at phase AssociationByScoreManagement | {e}"
            Utilities.notify_logging(message_telegram)
            raise ValueError
            
            