from Utilities.MultiException import ContinueGroupBetting
from Utilities import Utilities
from TaskManagement.GroupBettingManagement.AssociationByIP.AssociationByIPManagement import AssociationByIPManagement
from TaskManagement.GroupBettingManagement.PrepareData.PrepareDataManagement import PrepareDataManagement
from TaskManagement.GroupBettingManagement.AssociationByScore.AssociationByScoreManagement import AssociationByScoreManagement
from Configuration.Configuration import config
import time

class GroupBettingController(object):
    def run():
        initial = []
        month_prev = None
        day_prev = None
        year_prev = None
        while True:
            try:
                data_env = PrepareDataManagement(initial,month_prev,day_prev,year_prev)
                df_dataip, batch_cus_dict, daily_cus_dict, batch_cus_list, date_insert= data_env.run()
                
                association_ip = AssociationByIPManagement(df_dataip,date_insert,data_env)
                association_ip.run()
                
                association_score = AssociationByScoreManagement(data_env, batch_cus_dict, batch_cus_list, daily_cus_dict, date_insert)
                month_prev,day_prev,year_prev = association_score.run()
                
            except ContinueGroupBetting:
                continue
            except Exception as e:
                message_telegram = f"{config.ENV} | GroupBetting stopped"
                Utilities.notify_logging(message_telegram)
                break
            