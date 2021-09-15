from Utilities.MultiException import ContinueGroupBetting
from Utilities import Utilities
from TaskManagement.GroupBettingManagement.AssociationByIP.AssociationByIPManagement import AssociationByIPManagement
from TaskManagement.GroupBettingManagement.PrepareData.PrepareDataManagement import PrepareDataManagement
from TaskManagement.GroupBettingManagement.AssociationByScore.AssociationByScoreManagement import AssociationByScoreManagement
from Configuration.Configuration import config
import time
import multiprocessing as mp

class GroupBettingController(object):
    def run():
        initial = []
        month_prev = None
        day_prev = None
        year_prev = None
        time_start = time.time()
        among_of_data = 0
        #mp.set_start_method('spawn')
        while True:
            try:
                data_env = PrepareDataManagement(initial,month_prev,day_prev,year_prev,among_of_data)
                df_dataip, batch_cus_dict, daily_cus_dict, batch_cus_list, date_insert= data_env.run()
                print(type(date_insert))
                association_ip = AssociationByIPManagement(df_dataip,date_insert,data_env)
                association_ip.run()
                
                association_score = AssociationByScoreManagement(data_env, batch_cus_dict, batch_cus_list, daily_cus_dict, date_insert, time_start, data_env.among_of_data)
                month_prev,day_prev,year_prev,time_start,among_of_data = association_score.run()
                
            except ContinueGroupBetting:
                continue
            except Exception as e:
                message_telegram = f"{config.app_name} | {config.ENV} | INFO | GroupBetting stopped"
                Utilities.notify_logging(message_telegram)
                break
            