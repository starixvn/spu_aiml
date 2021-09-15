from DataAccess.DataAccessConnection import DataAccessConnection
from DataAccess.DataAccessConnection import spu_aiml,cts_datacenter
from datetime import datetime
import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import pandas as pd
import itertools
import time
import logging
import json
import numpy as np
from Utilities import Utilities
from DataAccess.Model.SPU_AIML.SPU_InsertCoupleIPStatsDAModel import SPU_InsertCoupleIPStatsDAModel
from DataAccess.Model.CTS_DataCenter.CTS_InsertAssociationByIPDAModel import CTS_InsertAssociationByIPDAModel
from DataAccess.CoreDA.BaseDA import BaseDA
from Configuration.Configuration import config


class AssociationByIPManagement(object):
    def __init__(self,*args):
        self.df_dataip = args[0]
        self.date_insert = args[1]
        self.data_env = args[2]

    def transform_to_listIP(self,df):
        keys, values1 = df.sort_values('sample_id').values.T
        ukeys, index = np.unique(keys, True)
        arrays = np.split(values1, index[1:])
        
        df2 = pd.DataFrame({'sample_id': ukeys, 'ip': [set(
            a) for a in arrays]})
        # print(df2)
        return df2

    def transform_to_listBettype(self,df):
        keys, values1 = df.sort_values('sample_id').values.T
        ukeys, index = np.unique(keys, True)
        arrays = np.split(values1, index[1:])
        df2 = pd.DataFrame({'sample_id': ukeys, 'bettype': [list(a) for a in arrays]})
        return df2
    
    def run(self):
        try:
            time_start = time.time()
            logging.info(f"{config.ENV} |Group Betting by IP is running")
            # message_telegram = f"{ENV} |Group Betting by IP is running"
            # SendLogTelegram.send_message(message_telegram)
            self.df_dataip = self.df_dataip[['custid','ip','bettype','matchid','leagueid','homeid','awayid','transdate']]
            self.AssociationbyIP(self.df_dataip,self.date_insert)
            logging.info(f'{config.app_name} | {config.ENV} | INFO | AssociationByIPManagement was completed in {time.time() - time_start} seconds ({round((time.time() - time_start)/3600,4)} hours)')
            del self.df_dataip
        except Exception as e:
            message_telegram = f"{config.app_name} | {config.ENV} | ERROR | Phase Association by IP | {e}"
            Utilities.notify_logging(message_telegram)
        
    def AssociationbyIP(self,df_dataip,date_insert):
        try:
            #time_start = time.time()
            
            #region: prepare homeID, awayID, LeagueID, EventDate,
            df_prepareData = df_dataip.groupby('matchid')[['leagueid','homeid','awayid','transdate']].first()
            df_prepareData.reset_index(inplace=True)
            #endregion

            #region: get all combination custid and get data come to dba
            df_uniquebettye = df_dataip.groupby(['matchid','ip','bettype','custid']).first()
            df_uniquebettye.reset_index(inplace=True)
            df_splitcustid = df_uniquebettye.groupby(['matchid','ip','bettype'])['custid'].agg(lambda x: list(itertools.combinations(x,2))).to_frame()
            
            df_splitcustid['usersnumber'] = df_splitcustid['custid'].str.len()
            df_splitcustid = df_splitcustid[df_splitcustid['usersnumber'] >= 1]
            df_splitcustid.reset_index(inplace=True)
            #df_groupbyip.reset_index(inplace=True)
            
            df_splitcustid['custid'] = df_splitcustid['custid'].agg(lambda x: list(x))
            if len(df_splitcustid.index) != 0:
                df_combicustid = pd.DataFrame(np.concatenate(df_splitcustid.custid), columns=['C1','C2']).reset_index(drop=True)
                df_combicustid['matchid'] = np.repeat(df_splitcustid.matchid.values, df_splitcustid['custid'].str.len())
                df_combicustid['ip'] = np.repeat(df_splitcustid.ip.values, df_splitcustid['custid'].str.len())
                df_combicustid['bettype'] = np.repeat(df_splitcustid.bettype.values, df_splitcustid['custid'].str.len())
                df_combicustid['sample_id'] = df_combicustid['C1'].map(str) + df_combicustid['C2'].map(str) + df_combicustid['matchid'].map(str)
                #endregion
                
                #region: concat unique list IP and count
                df_listAllIP = df_combicustid[['sample_id','ip']]
                df_listAllIP = self.transform_to_listIP(df_listAllIP)
                df_listAllIP['IPC'] = df_listAllIP['ip'].str.len()
                df_listAllIP['ip'] = [','.join(map(str, l)) for l in df_listAllIP['ip']]
                df_listAllIP.set_index('sample_id',inplace=True)
                #endregion
                
                #region: concat unique list bettype and count
                df_listAllBettype = df_combicustid[['sample_id','bettype']]
                df_listAllBettype = self.transform_to_listBettype(df_listAllBettype)
                df_listAllBettype['BTC'] = df_listAllBettype['bettype'].str.len()
                df_listAllBettype['bettype'] = df_listAllBettype['bettype'].apply(lambda x: set(x))
                df_listAllBettype['bettype'] = [','.join(map(str, l)) for l in df_listAllBettype['bettype']]
                df_listAllBettype.set_index('sample_id',inplace=True)
                #endregion
                
                #region: merge data list ip and bettype and take unique row
                df_combicustid = df_combicustid.groupby('sample_id').first()
                df_combicustid['ip'] = df_listAllIP['ip']
                df_combicustid['IPC'] = df_listAllIP['IPC']
                df_combicustid['bettype'] = df_listAllBettype['bettype']
                df_combicustid['BTC'] = df_listAllBettype['BTC']
                #endregion
                
                #region: get final result data and take it in to dba
                df_result = pd.merge(df_combicustid,df_prepareData, on='matchid')
                #df_resultbyIP = pd.merge(df_combicustid,df_groupIP, left_index=True, right_index=True)
                # change column name to transfer dba
                df_result = df_result.rename({
                    'matchid': 'M',
                    'homeid': 'H',
                    'awayid': 'A',
                    'leagueid': 'L',
                    'transdate': 'ED',
                    'bettype': 'BT',
                    'ip': 'IP'
                }, axis=1)
                
                fullDataIPSPU_dba = df_result.to_dict(orient="records")
                chunks1 = [fullDataIPSPU_dba[x:x+config.chunk_size]
                        for x in range(0, len(fullDataIPSPU_dba), config.chunk_size)]
                connection_spu = DataAccessConnection(spu_aiml)
                connection_cts = DataAccessConnection(cts_datacenter)
                for chunk in chunks1:
                    chunk = json.dumps(chunk)
                    ip_param = SPU_InsertCoupleIPStatsDAModel(chunk,date_insert)
                    dba_results = BaseDA.execute("SPU_AIML_InsertCoupleIPStats",spu_aiml,ip_param,connection_spu)
                    if config.transfer_ip:
                        if len(dba_results[0]) > 0:
                            df_CTS = pd.DataFrame(dba_results[0], columns=[
                            "C1",
                            "C2"])
                            fullDataIPCTS_dba = df_CTS.to_json(orient="records")
                            now = datetime.now()
                            current_time = now.strftime("%H:%M:%S")
                            #current_time = now.strftime('%Y-%m-%d %H:%M:%S')
                            datetime_insert = self.date_insert + " " + current_time
                            ip_param = CTS_InsertAssociationByIPDAModel(fullDataIPCTS_dba,datetime_insert)
                            BaseDA.execute("CTS_DC_Association_InsertAssociationByIP",cts_datacenter,ip_param,connection_cts)
                del connection_spu,connection_cts
                #logging.info(f"Group Betting by IP is done, total: {time.time() - time_start} seconds")
                #message_telegram = f"Group Betting by IP is done, total {round((time.time() - time_start)/3600,4)} hours "
                #SendLogTelegram.send_message(message_telegram)
                #endregion
        except Exception as e:
            raise ValueError("function AssociationbyIP | " + repr(e))
        

    