import logging
import multiprocessing as mp
import os
import time

from tqdm import tqdm

from Configuration.Configuration import config
from Controller.AssociationByScore.GroupBettingExtraction import ExtractInsightData


class DataPrepprocessingController:
    def run(self, batch_cus_dict):
        start_processing = time.time()

        candidates = os.listdir(os.path.join(config.root, config.match_breaking))
        pool = mp.Pool(config.nb_workers_phase_1)
        for _ in tqdm(pool.imap_unordered(ExtractInsightData.process_a_combination,
                                          [(candidate, batch_cus_dict) for candidate in candidates]),
                      total=len(candidates), desc='MAIN PROCESS'):
            pass
        pool.close()
        pool.join()
        print('\n',
              '********************************************************************************************************************************************')
        print("\n", f"{config.ENV} | PROCESSING TIME %.0f SECONDS" %
              (time.time() - start_processing))
        logging.info(
            f"{config.ENV} | Done phase 1, takes {time.time() - start_processing} seconds")
