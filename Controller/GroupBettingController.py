# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
# sys.path.append("D:\\Project\\aiml_cleancode\\")
import logging
import os
import time

from Controller.AssociationByIP.GroupbyIP import AssociationbyIP
from Controller.AssociationByScore.DataPreparation.DataPreparation import DataPreparationController
from Controller.AssociationByScore.DataPreprocessing.DataPreprocessing import DataPrepprocessingController
from Controller.ComputeGroupBetting.ComputeGroupBetting import ComputeGroupBettingController
from DataAccess.GroupBettingDA.AssociationStatsStaging import AssociationStatsStagingDA


def run(config):
    #reset old data for new run
    association_stats_staging_da = AssociationStatsStagingDA()
    association_stats_staging_da.truncate()
    data_preparation_controller = DataPreparationController()
    association_by_ip_controller = AssociationbyIP()
    preprocess_controller = DataPrepprocessingController()
    compute_group_betting_controller = ComputeGroupBettingController()
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
            # try:
                error, df_dataip, batch_cus_dict, batch_cus_list, daily_cus_dict = data_preparation_controller.run(orig_fn, check_files_sameday, date_insert)
                if error:
                    continue
            # except Exception as e:
            #     message_telegram = f"{config.ENV} | Error at phase 0: {e}"
            #     # FunctionSupport.notify_logging(message_telegram)
            #     print(message_telegram)
            #     break

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

            check_files = compute_group_betting_controller.wait_for_files()

            orig_fn = check_files[0]
            day_curr = orig_fn.split('.')[0].split('_')[2]
            date_item_container.append(day_curr)
            day_changed = int(day_curr) - int(day_prev)

            if day_changed:
                start_time = time.time()
                the_first_is_the_last = False

                if len(date_item_container) > 2:
                    try:
                        start_time = time.time()
                        BATCHES = compute_group_betting_controller.build_batches(batch_cus_list)
                        compute_group_betting_controller.process_batches(BATCHES, date_insert, daily_cus_dict)
                        logging.info(f'A BATCH of {date_insert} done in {time.time() - start_time} seconds')
                    except Exception as e:
                        message_telegram = f"{config.ENV} | Error phase 2 right before day end: {e}"
                        # Utilities.notify_logging(message_telegram)
                        print(message_telegram)
                        break
                else:
                    the_first_is_the_last = True
                print(f'{config.ENV} | date_insert when DAY END {date_insert}')

                daily_cus_list, daily_cus_dict = compute_group_betting_controller.get_daily_cus()

                compute_group_betting_controller.aggregate_day_end(daily_cus_list, daily_cus_dict, date_insert, the_first_is_the_last)

                print(
                    "***********************************************************************************************************************************************************************************")
                print("%s | AGG & INSERT TIME %.0f SECONDS" %
                      (config.ENV, time.time() - start_time))
                message_telegram = f"GROUP BETTING | {config.ENV} | Done, total {round((time.time() - time_begin) / 3600, 4)} hours "
                # Utilities.notify_logging(message_telegram,True)
                print(message_telegram)

                association_stats_staging_da = AssociationStatsStagingDA()
                association_stats_staging_da.truncate()

                compute_group_betting_controller.clean_cus_files()
                date_item_container = []
                continue
        else:
            time.sleep(config.time_sleep)
