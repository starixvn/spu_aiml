# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
# sys.path.append("D:\\Project\\aiml_cleancode\\")
import logging
import os
import pickle
import time

import numpy as np

from Controller.AssociationByIP.GroupbyIP import AssociationbyIP
from Controller.AssociationByScore.DataPreparation.DataPreparation import DataPreparationController
from Controller.AssociationByScore.DataPreprocessing.DataPreprocessing import DataPrepprocessingController
from Controller.Phase2Controller import Phase2Controller
from DataAccess.GroupBettingDA.AssociationStatsStaging import AssociationStatsStagingDA


def run(config):
    #reset old data for new run
    association_stats_staging_da = AssociationStatsStagingDA()
    association_stats_staging_da.truncate()
    data_preparation_controller = DataPreparationController()
    association_by_ip_controller = AssociationbyIP()
    preprocess_controller = DataPrepprocessingController()
    phase2_controller = Phase2Controller()
    date_item_container = []
    while True:
        check_files = [f for f in sorted(os.listdir(config.root_orig))]
        if len(check_files) > 0:
            orig_fn = check_files[0]
            check_files_sameday = data_preparation_controller.init_file_container(check_files)

            if not date_item_container:
                time_begin = time.time()
                date_item_container, date_insert, day_prev = data_preparation_controller.init_datetime(date_item_container, orig_fn)

            # START PHASE 0 --> PREPARATION
            # *****************************************************************************************************************************************************************************
            try:
                df_dataip, batch_cus_dict, batch_cus_list, daily_cus_dict = data_preparation_controller.run(orig_fn, check_files_sameday, date_insert)
                if not df_dataip:
                    continue
            except Exception as e:
                message_telegram = f"{config.ENV} | Error at phase 0: {e}"
                # FunctionSupport.notify_logging(message_telegram)
                print(message_telegram)
                break

            # START PHASE ASSOCIATION BY IP 
            # *****************************************************************************************************************************************************************************
            try:
                df_dataip = df_dataip[['custid','ip','bettype','matchid','leagueid','homeid','awayid','transdate']]
                association_by_ip_controller.run(df_dataip, date_insert, config)
                del df_dataip
            except Exception as e:
                message_telegram = f"{config.ENV} | Error at phase Association by IP: {e}"
                # FunctionSupport.notify_logging(message_telegram)
                print(message_telegram)
                break
            # END PHASE 0 - START PHASE 1
            # ****************************************************************************************************************************************************************************
            try:
                preprocess_controller.run(batch_cus_dict)
                date_item_container = []
            except Exception as e:
                message_telegram = f"{config.ENV} | Error phase 1: {e}"
                # FunctionSupport.notify_logging(message_telegram)
                print(message_telegram)
                break

            # END PHASE 1 - START PHASE 2
            # *****************************************************************************************************************************************************************************

            phase2_controller.run(date_item_container, time_begin)



        else:
            time.sleep(config.time_sleep)
