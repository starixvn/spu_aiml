import logging
import os
import pickle
import re
import time

import pandas as pd
from tqdm import tqdm

from Configuration.Configuration import config
from Helper import Utilities


def run(config, check_files):
    orig_fn = check_files[0]
    check_files_sameday = phase0_controller.init_file_container(check_files)

    if not date_item_container:
        time_begin = time.time()
        date_item_container, date_insert, day_prev  = phase0_controller.init_datetime(date_item_container, orig_fn)

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


def init_file_container(self, check_files):
    orig_fn = check_files[0]
    myStrCheck = orig_fn.rsplit("_", 4)
    pattern = "^" + myStrCheck[0]
    check_files_sameday = [i for i in check_files if re.findall(pattern, i)]
    return check_files_sameday

def init_datetime(self, date_item_container, orig_fn):
    month_prev = orig_fn.split('.')[0].split('_')[1]
    day_prev = orig_fn.split('.')[0].split('_')[2]
    year_prev = orig_fn.split('.')[0].split('_')[3]
    date_insert = year_prev+'-'+month_prev+'-'+day_prev
    logging.info(
        "======================================================================================================")
    logging.info(f"{config.ENV} | Running for Date: {date_insert}")
    message_telegram = f"GROUP BETTING | {config.ENV} | Running for {year_prev + '-' + month_prev + '-' + day_prev}"
    print(message_telegram)
    # Notifier.Telegram_send_message(message_telegram)
    date_item_container.append(day_prev)
    return date_item_container, date_insert, day_prev

def remove_file_from_live_folder(self, check_files_sameday):
    for file in check_files_sameday:
        os.rename(os.path.join(config.root_orig, file), os.path.join(config.backup, file))

def process_nan_data(self, data):
    df_nan = data[data[['custid', 'matchid', 'transdate', 'bettype', 'leagueid']].isna().any(axis=1)]
    if len(df_nan.index) != 0:
        data.to_csv(config.errorFolder + f"file_error_data_{time.time()}.csv", index=False)
        # count +=1
    data.dropna(subset=['custid', 'matchid', 'transdate', 'bettype', 'leagueid'], inplace=True)
    return data

def process_date_data(self, DATE):
    date_winlost = DATE['winlostdate'].min()
    DATE['category'] = DATE['category'].fillna(value='minor')
    DATE['category'] = DATE['category'].astype('str')
    DATE['category'] = DATE['category'].str.lower()
    DATE = DATE[['custid', 'matchid', 'transdate', 'bettype', 'leagueid', 'category']]
    date = DATE['transdate'].min()
    DATE['transdate'] = DATE['transdate'].apply(
        lambda z: Utilities.time_distance(Utilities.separate(date), Utilities.separate(z)))
    return DATE

def dump_check_cus_files(self, batch_cus_list, check_cus_files):
    if config.cus_list_fn not in check_cus_files:
        with open(os.path.join(config.root, config.cus_list_fn), 'wb') as f:
            pickle.dump(batch_cus_list, f)
    else:
        with open(os.path.join(config.root, config.cus_list_fn), 'rb') as f:
            daily_cus_list = pickle.load(f)
        daily_cus_list += batch_cus_list
        daily_cus_list = list(set(daily_cus_list))
        with open(os.path.join(config.root, config.cus_list_fn), 'wb') as f:
            pickle.dump(daily_cus_list, f)

def process_match_breaking(self, check_match_files, matches, DATE):
    if check_match_files:
        for fn in check_match_files:
            os.remove(os.path.join(config.root, config.match_breaking, fn))
    for n in tqdm(range(len(matches)), desc="MATCH BREAKING"):
        match = matches[n]
        m = DATE[DATE.matchid == match]
        for bt in [1, 3, 7, 8]:
            f = m[m.bettype == bt]
            if f.custid.nunique() > 1:
                f.to_csv(os.path.join(config.root, config.match_breaking,
                                        f"{match}_{bt}.csv"), index=False)

def build_combinations_cus_dict(self):
    batch_cus_dict = {}
    ls_mat = os.listdir(os.path.join(config.root, config.match_breaking))
    for k in tqdm(range(len(ls_mat)), desc="BUILD CUS DICT"):
        fn = ls_mat[k]
        match, bt = int(fn.split('.')[0].split('_')[0]), int(
            fn.split('.')[0].split('_')[1])
        df = pd.read_csv(os.path.join(config.root, config.match_breaking, fn))

        ls = df.custid.unique()
        for cus in ls:
            if cus not in batch_cus_dict:
                batch_cus_dict[cus] = [(match, bt)]
            else:
                batch_cus_dict[cus].append((match, bt))
    return batch_cus_dict

def dump_daily_cus_dict(self, batch_cus_dict, check_cus_files):
    if config.cus_dict_fn not in check_cus_files:
        with open(os.path.join(config.root, config.cus_dict_fn), 'wb') as g:
            pickle.dump(batch_cus_dict, g)
    else:
        with open(os.path.join(config.root, config.cus_dict_fn), 'rb') as g:
            daily_cus_dict = pickle.load(g)
        for key, value in batch_cus_dict.items():
            if key not in daily_cus_dict:
                daily_cus_dict[key] = value
            else:
                daily_cus_dict[key] += value
        with open(os.path.join(config.root, config.cus_dict_fn), 'wb') as g:
            pickle.dump(daily_cus_dict, g)
