from Utilities.MultiException import ContinueGroupBetting
from Utilities import Utilities
from TaskManagement.GroupBettingManagement.AssociationByScore.ComputeGroupBetting import ComputeGroupBetting
from TaskManagement.GroupBettingManagement.AssociationByScore.BuildDataModel import BuildDataModel
#from test import testmultiprocess
import logging
import time
from Configuration.Configuration import config


class AssociationByScoreManagement(object):
    def __init__(self,*args):
        self.data_env = args[0]
        self.batch_cus_dict = args[1]
        self.batch_cus_list = args[2]
        self.daily_cus_dict = args[3]
        self.date_insert = args[4]
        self.time_start = args[5]
        self.among_of_data = args[6]
        
    def run(self):
        try:
            calculate_data = BuildDataModel(self.batch_cus_dict)
            calculate_data.run()
            
            agg_score = ComputeGroupBetting(self.data_env, self.batch_cus_list, self.daily_cus_dict, self.date_insert, self.time_start)
            agg_score.run()
            
            if self.data_env.initial == []:
                message_telegram = f"{config.app_name} | {config.ENV} | INFO | AssociationByScoreManagement was completed in \n{int(time.time() - self.time_start)} seconds ({round((time.time() - self.time_start)/3600,2)} hours) \nTotal ticket: {self.among_of_data}"
                Utilities.notify_logging(message_telegram)
                self.time_start = time.time()
                self.among_of_data = 0
            return self.data_env.month_prev,self.data_env.day_prev,self.data_env.year_prev,self.time_start,self.among_of_data
        except ContinueGroupBetting:
                raise ContinueGroupBetting
        except Exception as e:
            message_telegram = f"{config.app_name} | {config.ENV} | ERROR | Phase AssociationByScoreManagement | {e}"
            Utilities.notify_logging(message_telegram)
            raise ValueError
            
            