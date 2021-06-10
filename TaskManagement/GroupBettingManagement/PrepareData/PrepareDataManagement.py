from DataAccess.CoreDA.CommonDA import CommonDA
import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from Configuration.Configuration import config
from Utilities.MultiException import ContinueGroupBetting
from Utilities.MultiException import ParentException
from Utilities.MultiException import ChildException
from DataAccess.Model.BaseDAModel import BaseDAModel
from DataAccess.Model.SPU_AIML.SPU_TruncateTableDAModel import SPU_TruncateTableDAModel
from DataAccess.CoreDA.BaseDA import BaseDA
import os
import re
import time
import logging
import pickle
import pandas as pd
from datetime import date as dt
from tqdm import tqdm
from Utilities import Utilities
from DataAccess.DataAccessConnection import spu_aiml,cts_datacenter
from DataAccess.DataAccessConnection import DataAccessConnection
import multiprocessing as mp


class PrepareDataManagement(object):
    def __init__(self, *args, **kwargs):
        self.initial = args[0]
        self.month_prev = args[1]
        self.day_prev = args[2]
        self.year_prev = args[3]
        
    def check_folder_file(self):
        try:
            check_files = [f for f in sorted(os.listdir(config.root_orig))]
            
            if len(check_files) > 0:
                check_files_sameday = Utilities.filter_files_by_day(check_files)
                filter_type = ".csv"
                check_files_sameday = Utilities.filter_files_by_type(check_files_sameday,filter_type)
                if len(check_files_sameday) > 0:
                    orig_fn = check_files_sameday[0]
                else:
                    raise ContinueGroupBetting
                
                if self.initial==[]:
                    self.month_prev=orig_fn.split('.')[0].split('_')[1]
                    self.day_prev=orig_fn.split('.')[0].split('_')[2]
                    self.year_prev=orig_fn.split('.')[0].split('_')[3]
                    logging.info(
                        "======================================================================================================")
                    message_telegram = f"{config.app_name} | {config.ENV} | INFO | Group Betting is running for {self.year_prev+'-'+self.month_prev+'-'+self.day_prev}"
                    Utilities.notify_logging(message_telegram,isInfo=True)
                    self.initial.append(self.day_prev)
                    
                return check_files_sameday,orig_fn
            else:
                raise ContinueGroupBetting
        except ContinueGroupBetting:
            raise ContinueGroupBetting
        except Exception as e:
            raise ValueError("function check_folder_file | " + repr(e))
        
    def clean_data(self,check_files_sameday,orig_fn):
        try:
            ### define time to start batch file
            logging.info(f'Start running new batch file')
            logging.info(f"Total file: {len(check_files_sameday)}")
            
            Utilities.change_permission_file(check_files_sameday)
            
            ### use list comprehensive to concat data
            data = pd.concat((pd.read_csv(os.path.join(config.root_orig, f),encoding='ISO-8859-1', skiprows=[1], skipfooter=1).assign(file_name = f) if (os.access(config.root_orig + f, os.R_OK) is True and os.access(config.root_orig + f, os.X_OK) is True) else Utilities.notify_logging(f"Error read file {f}") for f in check_files_sameday))
            
            ### move data was concat to backup folder
            Utilities.move_files(config.root_orig,config.backup,check_files_sameday)
            logging.info(f"Number of rows: {len(data)}")
            
            if len(data.index)==0:
                raise ContinueGroupBetting
            
            if data.bettype.isnull().values.any():
                logging.error(f'File Error {orig_fn} | Bettype Column Null')
                print(f'File Error {orig_fn} | Bettype Column Null')
                raise ContinueGroupBetting
            
            ### clean missing data
            data.dropna(subset=['custid', 'matchid', 'transdate', 'bettype','leagueid'],inplace=True)
            df_nan = data[data[['custid', 'matchid', 'transdate', 'bettype','leagueid']].isna().any(axis=1)]
            
            ### write error data to csv files
            if len(df_nan.index) != 0:
                data.to_csv(config.errorFolder+f"file_error_data_{time.time()}.csv",index=False)
                
            DATE = data[(data.bettype.isin([1, 3, 7, 8]))
                        & (data.liveindicator)]
            df_dataip = data[(data.bettype.isin([1, 3, 7, 8]))
                    & (data.liveindicator)]
            if len(DATE.index)==0:
                logging.error(f'File Error {orig_fn} | No Live')
                print(f'File Error {orig_fn} | No Live')
                raise ContinueGroupBetting
            
            return df_dataip, DATE, data
        except ContinueGroupBetting:
            raise ContinueGroupBetting
        except Exception as e:
            raise ValueError("function clean_data | " + repr(e))

    def dump_check_cus_files(self, batch_cus_list, check_cus_files):
        try:
            if config.cus_list_fn not in check_cus_files:
                with open(os.path.join(config.root, config.cus_list_fn), 'wb') as f:
                    pickle.dump(batch_cus_list, f)
            else:
                daily_cus_list = Utilities.load_a_file(config.root, config.cus_list_fn)
                
                daily_cus_list += batch_cus_list
                daily_cus_list = list(set(daily_cus_list))
                Utilities.save_a_file(config.root, config.cus_list_fn,daily_cus_list)
        except Exception as e:
            raise ChildException("function dump_check_cus_files | " + repr(e))

    def process_match_breaking(self, check_match_files, matches, DATE):
        try:
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
        except Exception as e:
            raise ChildException("function process_match_breaking | " + repr(e))
                    
    def build_combinations_cus_dict(self):
        try:
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
        except Exception as e:
            raise ChildException("function build_combinations_cus_dict | " + repr(e))
    
    def dump_daily_cus_dict(self, batch_cus_dict, check_cus_files):
        try:
            if config.cus_dict_fn not in check_cus_files:
                Utilities.save_a_file(config.root, config.cus_dict_fn,batch_cus_dict)
            else:
                daily_cus_dict = Utilities.load_a_file(config.root, config.cus_dict_fn)
                for key, value in batch_cus_dict.items():
                    if key not in daily_cus_dict:
                        daily_cus_dict[key] = value
                    else:
                        daily_cus_dict[key] += value
                Utilities.save_a_file(config.root, config.cus_dict_fn,daily_cus_dict)
        except Exception as e:
            raise ChildException("function dump_daily_cus_dict | " + repr(e))

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
                lambda z: Utilities.distance_time(Utilities.separate(date), Utilities.separate(z)))

            batch_cus_list = list(DATE.custid.unique())
            check_cus_files = os.listdir(os.path.join(config.root))
            self.dump_check_cus_files(batch_cus_list, check_cus_files)

            # match breaking
            matches = DATE.matchid.unique()
            check_match_files = os.listdir(os.path.join(config.root, config.match_breaking))
            self.process_match_breaking(check_match_files, matches, DATE)

            del DATE, data
            print('\n')

            # build cus_dict for count joining combinations
            batch_cus_dict = self.build_combinations_cus_dict()
            self.dump_daily_cus_dict(batch_cus_dict, check_cus_files)

            daily_cus_dict = Utilities.load_a_file(config.root, config.cus_dict_fn)
            
            return batch_cus_dict, daily_cus_dict, batch_cus_list, date_insert
        except ChildException as e:
            raise ValueError(e)
        except Exception as e:
            raise ValueError("function handling_data | " + repr(e))
        
    def clean_dataenv(self):
        try:
            connection_spu = DataAccessConnection(spu_aiml)
            ip_param = SPU_TruncateTableDAModel("AssociationStatsStaging")
            BaseDA.execute("SPU_AIML_DBA_Truncate_Table",spu_aiml,ip_param,connection_spu)
            del connection_spu
            check_cus_files=os.listdir(config.root)
            if config.cus_list_fn in check_cus_files:
                os.remove(os.path.join(config.root,config.cus_list_fn))
            if config.cus_dict_fn in check_cus_files:
                os.remove(os.path.join(config.root,config.cus_dict_fn))
        except Exception as e:
            raise ValueError("function clean_dataenv | " + repr(e))
            
    def run(self):
        try:
            
            time_phase0 = time.time()

            if self.initial == []:
                self.clean_dataenv()
                
            check_files_sameday, orig_fn = self.check_folder_file()
            df_dataip, DATE, data = self.clean_data(check_files_sameday,orig_fn)
            batch_cus_dict, daily_cus_dict, batch_cus_list, date_insert = self.handling_data(DATE,data,time_phase0)
            logging.info(f'{config.app_name} | {config.ENV} | INFO | PrepareDataManagement was completed in {time.time() - time_phase0} seconds ({round((time.time() - time_phase0)/3600,4)} hours)')
            return df_dataip, batch_cus_dict, daily_cus_dict, batch_cus_list, date_insert
            
        except ContinueGroupBetting:
            raise ContinueGroupBetting
        except Exception as e:
            message_telegram = f"{config.app_name} | {config.ENV} | ERROR | Phase PrepareDataManagement | {e}"
            Utilities.notify_logging(message_telegram)
            raise ValueError
            