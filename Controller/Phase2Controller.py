import logging
import multiprocessing as mp
import os
import pickle
import time

import numpy as np
from tqdm import tqdm

from Configuration.Configuration import config
from Controller.AssociationByScore.GroupBettingExtraction import AggDayEnd, AggOnTheFly
from DataAccess.GroupBettingDA.AssociationStatsStaging import AssociationStatsStagingDA
from DataAccess.GroupBettingDA.SystemParameter import SystemParameterDA


class Phase2Controller:
    def __init__(self):
        self.association_stats_staging_da = AssociationStatsStagingDA()

    def run_preprocess_before_aggregate(self, date_item_container, day_prev, batch_cus_list, date_insert, daily_cus_dict, time_begin):
        check_files = self.wait_for_files()
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
                    BATCHES = self.build_batches(batch_cus_list)
                    self.process_batches(BATCHES, date_insert, daily_cus_dict)
                    logging.info(f'A BATCH of {date_insert} done in {time.time() - start_time} seconds')
                except Exception as e:
                    message_telegram = f"{config.ENV} | Error phase 2 right before day end: {e}"
                    # FunctionSupport.notify_logging(message_telegram)
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

            self.aggregate_day_end(daily_cus_list, daily_cus_dict, date_insert, the_first_is_the_last)

            print(
                "***********************************************************************************************************************************************************************************")
            print("%s | AGG & INSERT TIME %.0f SECONDS" %
                  (config.ENV, time.time() - start_time))
            message_telegram = f"{config.ENV} | Group Betting is done, total {round((time.time() - time_begin) / 3600, 4)} hours "
            # FunctionSupport.notify_logging(message_telegram,True)
            print(message_telegram)
            self.association_stats_staging_da.truncate()

            self.clean_cus_files()
            continue
        try:
            start_time = time.time()
            self.aggregate_on_the_fly(batch_cus_list, daily_cus_dict, date_insert)
            logging.info(f'{config.ENV} | Done phase 2, takes {time.time() - start_time} seconds')
        except Exception as e:
            message_telegram = f"{config.ENV} | Error phase 2: {e}"
            # FunctionSupport.notify_logging(message_telegram)
            print(message_telegram)
            break

    def wait_for_files(self):
        check_files = [f for f in sorted(os.listdir(config.root_orig))]
        while len(check_files) == 0:
            time.sleep(config.time_sleep)
            check_files = [f for f in sorted(os.listdir(config.root_orig))]
        return check_files

    def build_batches(self, batch_cus_list):
        batch_cus_list = sorted(batch_cus_list)
        BATCHES = [','.join([str(z) for z in batch_cus_list[x:x + config.num_batch_cus]]) for x in
                   range(0, len(batch_cus_list), config.num_batch_cus)]
        logging.info(f"number of cust list: {len(batch_cus_list)}")
        return BATCHES

    def process_batches(self, BATCHES, date_insert, daily_cus_dict):
        pool = mp.Pool(config.nb_workers_phase_2)
        for _ in tqdm(
                pool.imap_unordered(AggOnTheFly.aggregate, [(BATCH, date_insert, daily_cus_dict) for BATCH in BATCHES]),
                total=len(BATCHES), desc=f'AGG | A BATCH OF {date_insert}'):
            pass
        pool.close()
        pool.join()

    def aggregate_day_end(self, daily_cus_list, daily_cus_dict, date_insert, the_first_is_the_last):

        BATCHES = [daily_cus_list[x:x + config.num_batch_cus] for x in
                   range(0, len(daily_cus_list), config.num_batch_cus)]
        pool = mp.Pool(config.nb_workers_phase_2)
        for _ in tqdm(pool.imap_unordered(AggDayEnd.day_end_aggregate,
                                          [(min(BATCH), max(BATCH), date_insert, the_first_is_the_last, daily_cus_dict)
                                           for BATCH in BATCHES]), total=len(BATCHES), desc='DAY-END AGG'):
            pass
        pool.close()
        pool.join()
        system_parameter_da = SystemParameterDA()
        system_parameter_da.insert(date_insert)

    def clean_cus_files(self):
        check_cus_files = os.listdir(config.root)
        if config.cus_list_fn in check_cus_files:
            os.remove(os.path.join(config.root, config.cus_list_fn))
        if config.cus_dict_fn in check_cus_files:
            os.remove(os.path.join(config.root, config.cus_dict_fn))

    def aggregate_on_the_fly(self, batch_cus_list, daily_cus_dict, date_insert):
        batch_cus_list = sorted(batch_cus_list)
        BATCHES = [batch_cus_list[x:x + config.num_batch_cus] for x in
                   range(0, len(batch_cus_list), config.num_batch_cus)]
        logging.info("*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*/*")
        logging.info(f"number of cust list: {len(batch_cus_list)}")
        pool = mp.Pool(config.nb_workers_phase_2)

        for _ in tqdm(
                pool.imap_unordered(AggOnTheFly.aggregate, [(BATCH, date_insert, daily_cus_dict) for BATCH in BATCHES]),
                total=len(BATCHES), desc='AGG'):
            pass
        pool.close()
        pool.join()
