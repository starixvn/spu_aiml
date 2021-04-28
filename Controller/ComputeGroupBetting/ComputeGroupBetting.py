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


class ComputeGroupBettingController:
    def __init__(self):
        self.association_stats_staging_da = AssociationStatsStagingDA()

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

    def get_daily_cus(self):
        with open(os.path.join(config.root, config.cus_list_fn), 'rb') as f:
            daily_cus_list = pickle.load(f)
        with open(os.path.join(config.root, config.cus_dict_fn), 'rb') as g:
            daily_cus_dict = pickle.load(g)
        daily_cus_list = np.sort(daily_cus_list)
        return daily_cus_list, daily_cus_dict
