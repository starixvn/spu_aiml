# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
# sys.path.append("D:\\Project\\aiml_cleancode\\")
import logging
import multiprocessing as mp
import os
import pickle
import time

import numpy as np
import pandas as pd
from tqdm import tqdm

from DataAccess.GroupBettingDA.SPU_AIML.AssociationStatsStaging import AssociationStatsStagingDA
from Controller.AssociationByIP import GroupbyIP
from Controller.AssociationByScore import ExtractInsightData
from Controller.PreprocessDataController import PreprocessData

from Controller.ComputeGroupBetting.ComputeGroupBetting import ComputeGroupBettingController


def run(config):
    
    # Reset old data for new run
    association_stats_staging_da = AssociationStatsStagingDA()
    association_stats_staging_da.truncate()

    phase0_controller = PreprocessData()
    phase2_controller = ComputeGroupBettingController()
    date_item_container = []

    while True:
        check_files = [f for f in sorted(os.listdir(config.root_orig))]
        if len(check_files) > 0:
            orig_fn = check_files[0]
            check_files_sameday = phase0_controller.init_file_container(check_files)

            if not date_item_container:
                time_begin = time.time()
                date_item_container, date_insert, day_prev  = phase0_controller.init_datetime(date_item_container, orig_fn)

            # START PREPARING DATA
            # *****************************************************************************************************************************************************************************
            try:
                time_phase0 = time.time()
                t = time.localtime()
                current_time = time.strftime("%H:%M:%S", t)
                
                print(f"{config.ENV} | CURRENT TIME : ", current_time)
                logging.info(f'Start running file {orig_fn}')
                logging.info(f"Total file: {len(check_files_sameday)}")
                
                ### use list comprehensive to concat data
                # data = pd.concat((pd.read_csv(os.path.join(config.root_orig, f),encoding='ISO-8859-1', skiprows=[1], skipfooter=1).assign(file_name = f) if (os.access(config.root_orig + f, os.R_OK) is True and os.access(config.root_orig + f, os.X_OK) is True) else Utilities.notify_logging(f"Error read file {f}") for f in check_files_sameday))
                data = pd.concat((pd.read_csv(os.path.join(config.root_orig, f),encoding='ISO-8859-1', skiprows=[1], skipfooter=1).assign(file_name = f) if (os.access(config.root_orig + f, os.R_OK) is True and os.access(config.root_orig + f, os.X_OK) is True) else print(f"Error read file {f}") for f in check_files_sameday))

                phase0_controller.remove_file_from_live_folder(check_files_sameday)

                logging.info(f"Number of rows: {len(data)}")
                
                if data.empty:
                    continue
                
                if data.bettype.isnull().values.any():
                    logging.error(f'File Error {orig_fn} | Bettype Column Null')
                    print(f'File Error {orig_fn} | Bettype Column Null')
                    continue
                
                ### clean missing data
                data = phase0_controller.process_nan_data(data)
                if data.empty:
                    continue

                df_dataip = data[(data.bettype.isin([1, 3, 7, 8]))
                                 & (data.liveindicator)]
                print(f"date insert {date_insert}")

                DATE = data[(data.bettype.isin([1, 3, 7, 8]))
                            & (data.liveindicator)]
                DATE = phase0_controller.process_date_data(DATE)


                batch_cus_list = list(DATE.custid.unique())
                check_cus_files = os.listdir(os.path.join(config.root))
                phase0_controller.dump_check_cus_files(batch_cus_list, check_cus_files)

                # match breaking
                matches = DATE.matchid.unique()
                check_match_files = os.listdir(os.path.join(config.root, config.match_breaking))
                phase0_controller.process_match_breaking(check_match_files, matches, DATE)

                del DATE, data
                print('\n')

                # build cus_dict for count joining combinations
                batch_cus_dict = phase0_controller.build_combinations_cus_dict()
                phase0_controller.dump_daily_cus_dict(batch_cus_dict, check_cus_files)

                with open(os.path.join(config.root, config.cus_dict_fn), 'rb') as g:
                        daily_cus_dict = pickle.load(g)
                logging.info(
                    f"{config.ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
            except Exception as e:
                message_telegram = f"{config.ENV} | Error at phase 0: {e}"
                # Utilities.notify_logging(message_telegram)
                print(message_telegram)
                break

            # START COMPUTING ASSOCIATION BY IP 
            # *****************************************************************************************************************************************************************************
            try:
                logging.info(f"{config.ENV} |Group Betting by IP is running")
                # message_telegram = f"{ENV} |Group Betting by IP is running"
                # Notifier.Telegram_send_message(message_telegram)
                df_dataip = df_dataip[['custid','ip','bettype','matchid','leagueid','homeid','awayid','transdate']]
                GroupbyIP.run(df_dataip, date_insert, config)
                del df_dataip
            except Exception as e:
                message_telegram = f"{config.ENV} | Error at phase Association by IP: {e}"
                # Utilities.notify_logging(message_telegram)
                print(message_telegram)
                break

            # START PREPROCESSING DATA
            # ****************************************************************************************************************************************************************************
            try:
                start_processing = time.time()

                candidates = os.listdir(os.path.join(config.root, config.match_breaking))
                pool = mp.Pool(config.nb_workers_phase_1)
                for _ in tqdm(pool.imap_unordered(ExtractInsightData.process_a_combination, [(candidate, batch_cus_dict) for candidate in candidates]), total=len(candidates), desc='MAIN PROCESS'):
                    pass
                pool.close()
                pool.join()
                print('\n', '********************************************************************************************************************************************')
                print("\n", f"{config.ENV} | PROCESSING TIME %.0f SECONDS" %
                    (time.time() - start_processing))
                logging.info(
                    f"{config.ENV} | Done phase 1, takes {time.time() - start_processing} seconds")
            except Exception as e:
                message_telegram = f"{config.ENV} | Error phase 1: {e}"
                # Utilities.notify_logging(message_telegram)
                print(message_telegram)
                break

            # START COMPUTING GROUP BETTING
            # *****************************************************************************************************************************************************************************
            check_files = phase2_controller.wait_for_files()

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
                        BATCHES = phase2_controller.build_batches(batch_cus_list)
                        phase2_controller.process_batches(BATCHES, date_insert, daily_cus_dict)
                        logging.info(f'A BATCH of {date_insert} done in {time.time() - start_time} seconds')
                    except Exception as e:
                        message_telegram = f"{config.ENV} | Error phase 2 right before day end: {e}"
                        # Utilities.notify_logging(message_telegram)
                        print(message_telegram)
                        break
                else:
                    the_first_is_the_last = True
                print(f'{config.ENV} | date_insert when DAY END {date_insert}')

                with open(os.path.join(config.root, config.cus_list_fn), 'rb') as f:
                    daily_cus_list = pickle.load(f)
                with open(os.path.join(config.root, config.cus_dict_fn), 'rb') as g:
                    daily_cus_dict = pickle.load(g)
                daily_cus_list = np.sort(daily_cus_list)

                phase2_controller.aggregate_day_end(daily_cus_list, daily_cus_dict, date_insert, the_first_is_the_last)

                print("***********************************************************************************************************************************************************************************")
                print("%s | AGG & INSERT TIME %.0f SECONDS" %
                    (config.ENV,time.time() - start_time))
                message_telegram = f"GROUP BETTING | {config.ENV} | Done, total {round((time.time() - time_begin)/3600,4)} hours "
                # Utilities.notify_logging(message_telegram,True)
                print(message_telegram)

                association_stats_staging_da = AssociationStatsStagingDA()
                association_stats_staging_da.truncate()

                phase2_controller.clean_cus_files()
                date_item_container = []
                continue

            try:
                start_time = time.time()
                phase2_controller.aggregate_on_the_fly(batch_cus_list, daily_cus_dict, date_insert)
                logging.info(f'{config.ENV} | Done phase 2, takes {time.time()-start_time} seconds')
            except Exception as e:
                message_telegram = f"{config.ENV} | Error phase 2: {e}"
                # Utilities.notify_logging(message_telegram)
                print(message_telegram)
                break
        else:
            time.sleep(config.time_sleep)
