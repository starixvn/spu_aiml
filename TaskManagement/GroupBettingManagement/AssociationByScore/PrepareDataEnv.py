from app import config
import os
import re
import time
import logging
import pickle
import datetime
import pandas as pd
from datetime import date as dt
from tqdm import tqdm
from Helper import SendLogTelegram
from Utilities import FunctionSupport

class PrepareDataEnv(object):
    def __init__(self, *args, **kwargs):
        self.initial = args[0]
    
    def separate(transdate):
        """
        >>> Input  :    '2020-09-26 7:31:01.872'

        >>> Output :    (2020,9,26,7,31,1)
        """
        date, hms = transdate.split(' ')[0].split(
            '-'), transdate.split(' ')[1].split('.')[0].split(':')
        year, month, day = int(date[0]), int(date[1]), int(date[2])
        hour, min, sec = int(hms[0]), int(hms[1]), int(hms[2])
        return (year, month, day, hour, min, sec)
    
    def distance_time(transdate1, transdate2):
        """
        >>> Input  : transdate 1 : datetime.datetime(2020,9,26,7,28,1)

                    transdate 2 : datetime.datetime(2020,9,26,7,31,1)

        >>> Output : 180 seconds
        """

        return (datetime.datetime(*transdate2)-datetime.datetime(*transdate1)).total_seconds()
        
    def check_folder_file(self):
        isHaveFile = False
        check_files = [f for f in sorted(os.listdir(config.root_orig))]
        if len(check_files) > 0:
            isHaveFile = True
            orig_fn = check_files[0]
            myStrCheck = check_files[0].rsplit("_",4)
            pattern = "^" + myStrCheck[0]
            check_files_sameday = [i for i in check_files if re.findall(pattern,i)]
            if self.initial==[]:
                month_prev=orig_fn.split('.')[0].split('_')[1]
                day_prev=orig_fn.split('.')[0].split('_')[2]
                year_prev=orig_fn.split('.')[0].split('_')[3]
                time_begin = time.time()
                today = dt.today()
                logging.info(
                    "======================================================================================================")
                logging.info(f"{config.ENV} | Running for Date: {year_prev+'-'+month_prev+'-'+day_prev}")
                message_telegram = f"{config.ENV} | Group Betting is running for {year_prev+'-'+month_prev+'-'+day_prev}"
                SendLogTelegram.send_message(message_telegram)
                self.initial.append(day_prev)
            return isHaveFile,check_files_sameday,orig_fn
        return isHaveFile,None,None
                
                
    def clean_data(self,check_files_sameday,orig_fn):
        
        t = time.localtime()
        current_time = time.strftime("%H:%M:%S", t)
        
        print(f"{config.ENV} | CURRENT TIME : ", current_time)
        logging.info(f'Start running file {orig_fn}')
        logging.info(f"Total file: {len(check_files_sameday)}")
        
        ### use list comprehensive to concat data
        data = pd.concat((pd.read_csv(os.path.join(config.root_orig, f),encoding='ISO-8859-1', skiprows=[1], skipfooter=1).assign(file_name = f) if (os.access(config.root_orig + f, os.R_OK) is True and os.access(config.root_orig + f, os.X_OK) is True) else FunctionSupport.notify_logging(f"Error read file {f}") for f in check_files_sameday))
        
        for file in check_files_sameday:
            os.rename(os.path.join(config.root_orig,file),os.path.join(config.backup,file))
        logging.info(f"Number of rows: {len(data)}")
        
        isContinue = False
        if len(data.index)==0:
            isContinue = True
            return None,None,isContinue
        
        if data.bettype.isnull().values.any():
            logging.error(f'File Error {orig_fn} | Bettype Column Null')
            print(f'File Error {orig_fn} | Bettype Column Null')
            isContinue = True
            return None,None,isContinue
        
        ### clean missing data
        data.dropna(subset=['custid', 'matchid', 'transdate', 'bettype','leagueid'],inplace=True)
        df_nan = data[data[['custid', 'matchid', 'transdate', 'bettype','leagueid']].isna().any(axis=1)]
        
        if len(df_nan.index) != 0:
            data.to_csv(config.errorFolder+f"file_error_data_{time.time()}.csv",index=False)
            #count +=1
        DATE = data[(data.bettype.isin([1, 3, 7, 8]))
                    & (data.liveindicator)]
        df_dataip = data[(data.bettype.isin([1, 3, 7, 8]))
                & (data.liveindicator)]
        if len(DATE.index)==0:
            logging.error(f'File Error {orig_fn} | No Live')
            print(f'File Error {orig_fn} | No Live')
            isContinue = True
            return None,None,isContinue
        return isContinue, df_dataip, DATE, data
        
    def load_a_file(self,location,file_name):
        with open(os.path.join(location, file_name), 'rb') as f:
            my_file = pickle.load(f)
        return my_file

    def save_a_file(self,location,file_name,object):
        with open(os.path.join(location, file_name), 'wb') as f:
            pickle.dump(object,f)

    def build_match_breaking(self,matches,DATE):
        # match breaking
        check_match_files=os.listdir(os.path.join(config.root, config.match_breaking))
        if len(check_match_files)>0:
            for fn in check_match_files:
                os.remove(os.path.join(config.root, config.match_breaking,fn))
        for n in tqdm(range(len(matches)), desc="MATCH BREAKING"):
            match = matches[n]
            m = DATE[DATE.matchid == match]
            for bt in [1, 3, 7, 8]:
                f = m[m.bettype == bt]
                if f.custid.nunique() > 1:
                    f.to_csv(os.path.join(config.root, config.match_breaking,
                                        f"{match}_{bt}.csv"), index=False)
                    
    def build_batch_cus_dict(location,decomposed_folder):
        batch_cus_dict = {}
        list_of_matches = os.listdir(os.path.join(location, decomposed_folder))
        for k in range(len(list_of_matches)):
            fn = list_of_matches[k]
            match, bt = int(fn.split('.')[0].split('_')[0]), int(
                fn.split('.')[0].split('_')[1])
            df = pd.read_csv(os.path.join(location, decomposed_folder, fn))

            ls = df.custid.unique()
            for cus in ls:
                if cus not in batch_cus_dict:
                    batch_cus_dict[cus] = [(match, bt)]
                else:
                    batch_cus_dict[cus].append((match, bt))
        return batch_cus_dict

    def build_daily_cus_dict(self,location, file_name, batch_cus_dict):
        check_cus_files = os.listdir(os.path.join(location))
        if file_name not in check_cus_files:
            self.save_a_file(location, file_name, batch_cus_dict)
            return batch_cus_dict
        else:
            daily_cus_dict = self.load_a_file(location, file_name)
            for key,value in batch_cus_dict.items():
                if key not in daily_cus_dict:
                    daily_cus_dict[key] = value
                else:
                    daily_cus_dict[key] += value
            self.save_a_file(location, file_name ,daily_cus_dict)
            daily_cus_dict = self.load_a_file(location, file_name)
            return daily_cus_dict

    def build_daily_cus_list(self,location, file_name, batch_cus_list):
        check_cus_files=os.listdir(os.path.join(location))
        if file_name not in check_cus_files:
            self.save_a_file(location, file_name, batch_cus_list)
            return batch_cus_list
        else:
            daily_cus_list = self.load_a_file(location, file_name)
            daily_cus_list += batch_cus_list
            daily_cus_list = list(set(daily_cus_list))
            self.save_a_file(location, file_name, daily_cus_list)
            return daily_cus_list

    def handling_data(self,DATE,data,time_phase0):
        try:
            date_winlost = DATE['winlostdate'].min()
            DATE['category'] = DATE['category'].fillna(value='minor')
            DATE['category'] = DATE['category'].astype('str')
            DATE['category'] = DATE['category'].str.lower()
            DATE = DATE[['custid', 'matchid', 'transdate', 'bettype','leagueid','category']]
            date = DATE['transdate'].min()
            date_insert = date_winlost.split()[0]
            # date_insert='2021-01-29'
            print(f"date insert {date_insert}")
            DATE['transdate'] = DATE['transdate'].apply(
                lambda z: FunctionSupport.distance_time(FunctionSupport.separate(date), FunctionSupport.separate(z)))

            # get list of matches
            matches = DATE.matchid.unique()

            # get list of custid
            daily_cus_list = self.build_daily_cus_list()

            self.build_match_breaking(matches,DATE)
            del DATE, data
            batch_cus_dict = self.build_batch_cus_dict(daily_cus_list)
            daily_cus_dict = self.build_daily_cus_dict()
            logging.info(
                f"{config.ENV} | Done phase 0, takes {time.time() - time_phase0} seconds")
            # print('\n',f"MATCH BREAKING TAKES {(time.time()-start_match_breaking)} seconds")
            return batch_cus_dict, daily_cus_dict, date_insert
        except Exception as e:
            message_telegram = f"{config.ENV} | Error at phase 0: {e}"
            FunctionSupport.notify_logging(message_telegram)
            
        
    def run(self):
        time_phase0 = time.time()
        isHaveFile,check_files_sameday,orig_fn = self.check_folder_file()
        if isHaveFile:
            isContinue, df_dataip, DATE, data = self.clean_data(check_files_sameday,orig_fn)
            if isContinue:
                return None,None,None,None,None,isContinue
            batch_cus_dict, daily_cus_dict, date_insert = self.handling_data(DATE,data,time_phase0)
            return df_dataip, date_insert,batch_cus_dict, daily_cus_dict,isContinue
        return None,None,None,None,None,not(isHaveFile)
            