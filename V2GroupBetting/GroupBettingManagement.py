import time
import os
import re
import multiprocessing as mp
from tqdm import tqdm
from Utilities import build_data,distance_time,separate,decompose_into_combinations
from Utilities import build_batch_cus_dict,build_daily_cus_dict,build_daily_cus_list
from Utilities import ExtractInsightsFromData,Aggregate
# from DataAccess import GroupBettingDataAccess

class GroupBettingManagement():
    # def __init__(self):
    #     pass

    def read_and_clean_data(args):
        initial,config = args
        try:
            # read - filter - preprocess data
            check_files = [f for f in sorted(os.listdir(config.root_orig))]
            if len(check_files) > 0:
                orig_fn = check_files[0]
                myStrCheck = check_files[0].rsplit("_",4)
                pattern = "^" + myStrCheck[0]
                check_files_sameday = [i for i in check_files if re.findall(pattern,i)]
                data = build_data((check_files_sameday,config))
                if len(data.index)==0 or data.bettype.isnull().values.any():
                    # os.remove(os.path.join(config.root_orig, config.orig_fn))
                    return None
                DATE = data[(data.bettype.isin([1, 3, 7, 8]))
                            & (data.liveindicator)]
                if len(DATE.index)==0:
                    # os.remove(os.path.join(config.root_orig, config.orig_fn))
                    return None
                month = orig_fn.split('.')[0].split('_')[1]
                day = orig_fn.split('.')[0].split('_')[2]
                year = orig_fn.split('.')[0].split('_')[3]
                if initial==[]:
                    # logging.info(
                    #     "======================================================================================================")
                    # logging.info(f"{ENV} | Running for Date: {year_prev+'-'+month_prev+'-'+day_prev}")
                    print("======================================================================================================")
                    print(f"{config.ENV} | Running for Date: {year+'-'+month+'-'+day}")
                    print('day_prev {0}'.format(day))
                    # message_telegram = f"{ENV} | Group Betting is running for {year_prev+'-'+month_prev+'-'+day_prev}"
                    # SendLogTelegram.send_message(message_telegram)
                    initial.append(day)
                return DATE,initial,month,day,year
            else:
                return None

            
        except Exception as e:
            # logging.error(f"{ENV} | Error at phase 0: {e}")
            print(f"{config.ENV} | Error in read_and_clean_data function: {e}")
            # message_telegram = f"{ENV} | Error at phase 0: {e}"
            # SendLogTelegram.send_message(message_telegram)
    
    def preprocess_data_and_prepare_necessary_files(args):
        DATE,time_phase0,config = args
        date_winlost = DATE['winlostdate'].min()
        DATE['category'] = DATE['category'].fillna(value='minor')
        DATE['category'] = DATE['category'].str.lower()
        DATE = DATE[['custid', 'matchid', 'transdate', 'bettype','leagueid','category']]
        date = DATE['transdate'].min()
        date_insert = date_winlost.split()[0]
        # date_insert='2021-01-29'
        # print(f"date insert {date_insert}")
        DATE['transdate'] = DATE['transdate'].apply(
            lambda z: distance_time(separate(date), separate(z)))


        # get list of custid
        batch_cus_list = list(DATE.custid.unique())
        
        # build daily_cus_list
        daily_cus_list = build_daily_cus_list(config.root, config.cus_list_fn, batch_cus_list)

        # combination decomposition | combination = (match,bettype)
        decompose_into_combinations(config.root ,config.match_breaking, DATE)

        del DATE
        print('\n')

        # build batch_cus_dict for count joining combinations
        batch_cus_dict = build_batch_cus_dict(config.root, config.match_breaking)
        
        # build daily_cus_dict
        daily_cus_dict = build_daily_cus_dict(config.root, config.cus_dict_fn, batch_cus_dict)
        # logging.info(
        #     f"{ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
        print(f"{config.ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
        # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
        return batch_cus_dict, batch_cus_list, daily_cus_dict, daily_cus_list, date_insert
    
    def do_phase_1(args):
        batch_cus_dict, date_insert, config = args
        try:
            start_time = time.time()

            candidates = os.listdir(os.path.join(config.root, config.match_breaking))
            pool = mp.Pool(config.nb_workers_phase_1)
            for _ in tqdm(pool.imap_unordered(ExtractInsightsFromData.extract_insights_from_data, 
                        [(candidate, batch_cus_dict, config) for candidate in candidates]),
                        total=len(candidates), desc=f'PAIRWISE | A BATCH OF {date_insert}'):
                pass
            pool.close()
            pool.join()
            print(f"{config.ENV} | Done phase 1, takes {time.time() - start_time} seconds")
        except Exception as e:
            # logging.error(f"{ENV} | Error phase 1: {e}")
            print(f"{config.ENV} | Error in do_phase_1 function: {e}")
            # message_telegram = f"{ENV} | Error phase 1: {e}"
            # SendLogTelegram.send_message(message_telegram)
    
    def do_phase_2(args):
        batch_cus_list, daily_cus_dict, date_insert, the_first_is_the_last, config = args
        try:
            start_time = time.time()

            # build batches
            batch_cus_list = sorted(batch_cus_list)
            BATCHES = [','.join([str(z) for z in batch_cus_list[x:x+config.num_batch_cus]]) for x in range(0, len(batch_cus_list), 
                        config.num_batch_cus)]
            # logging.info(f"number of cust list: {len(batch_cus_list)}")
            print(f"number of cust list: {len(batch_cus_list)}")
            pool = mp.Pool(config.nb_workers_phase_2)
            for _ in tqdm(pool.imap_unordered(Aggregate.aggregate, [(BATCH, date_insert, daily_cus_dict, the_first_is_the_last, config) for BATCH in BATCHES]),
                            total=len(BATCHES),desc=f'AGG | A BATCH OF {date_insert}'):
                pass
            pool.close()
            pool.join()
            print(f'A BATCH of {date_insert} done in {time.time()-start_time} seconds')

        except Exception as e:
            # logging.error(f"{ENV} | Error phase 2: {e}")
            print(f"{config.ENV} | Error in do_phase_2 function: {e}")
            # message_telegram = f"{ENV} | Error phase 2: {e}"
            # SendLogTelegram.send_message(message_telegram)
    
    def finalize(args):
        daily_cus_list, date_insert, daily_cus_dict, the_first_is_the_last, config = args
        BATCHES = [daily_cus_list[x:x+config.num_batch_cus] for x in range(0, len(daily_cus_list), config.num_batch_cus)]
        pool = mp.Pool(config.nb_workers_phase_2)
        for _ in tqdm(pool.imap_unordered(Aggregate.aggregate_when_day_end, [(min(BATCH),max(BATCH), date_insert, daily_cus_dict,
                                                                            the_first_is_the_last, config) 
                                        for BATCH in BATCHES])
                                        , total=len(BATCHES), desc='DAY-END AGG'):
            pass
        pool.close()
        pool.join()