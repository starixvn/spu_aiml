import pandas as pd
import itertools
import time
import logging
import json
import numpy as np
from GroupBetting import SendLogTelegram
from mysql.connector import MySQLConnection
def transform_to_listIP(df):
    keys, values1 = df.sort_values('sample_id').values.T
    ukeys, index = np.unique(keys, True)
    arrays = np.split(values1, index[1:])
    
    df2 = pd.DataFrame({'sample_id': ukeys, 'ip': [set(
        a) for a in arrays]})
    # print(df2)
    return df2

def transform_to_listBettype(df):
    keys, values1 = df.sort_values('sample_id').values.T
    ukeys, index = np.unique(keys, True)
    arrays = np.split(values1, index[1:])
    
    df2 = pd.DataFrame({'sample_id': ukeys, 'bettype': [list(a) for a in arrays]})
    
    # print(df2)
    return df2
def get_unique_bettype(x):
    #print(x)
    list_bettype = [i.split(',') for i in x]
    result = list(itertools.chain.from_iterable(list_bettype))
    counts = len(result)
    result = set(result)
    return pd.Series((result,counts))

def AssociationbyIP(df_dataip,chunk_size,date_insert):
    try:
        time_start = time.time()
        
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
            df_listAllIP = transform_to_listIP(df_listAllIP)
            #print(df_listAllIP.head())
            df_listAllIP['IPC'] = df_listAllIP['ip'].str.len()
            #print(df_listAllIP.head())
            df_listAllIP['ip'] = [','.join(map(str, l)) for l in df_listAllIP['ip']]
            df_listAllIP.set_index('sample_id',inplace=True)
            #endregion
            
            #region: concat unique list bettype and count
            df_listAllBettype = df_combicustid[['sample_id','bettype']]
            df_listAllBettype = transform_to_listBettype(df_listAllBettype)
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
            chunks1 = [fullDataIPSPU_dba[x:x+chunk_size]
                    for x in range(0, len(fullDataIPSPU_dba), chunk_size)]
            
            try:
                conn = MySQLConnection(user='aimlServiceAdmin', password='aimlServiceAdmin@AIML2209#',
                                            host='10.40.40.78', port='3306', database='SPU_AIML')
                cur = conn.cursor()
                for chunk1 in chunks1:
                    json_objIP1 = json.dumps(chunk1)
                    cur.callproc('SPU_AIML.SPU_AIML_InsertCoupleIPStats',[json_objIP1,None])
                    dba_results = [r.fetchall() for r in cur.stored_results()]
                    conn.commit()
                    
                    if len(dba_results[0]) > 0:
                        df_CTS = pd.DataFrame(dba_results[0], columns=[
                        "C1",
                        "C2"])
                        fullDataIPCTS_dba = df_CTS.to_json(orient="records")
                        try:
                            conn2 = MySQLConnection(user='ctsServiceAdmin', password='ctsServiceAdmin@CTS2209#',
                                        host='10.40.40.58', port='3306', database='CTS_DataCenter')
                            cur2 = conn2.cursor()
                            cur2.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByIP',[fullDataIPCTS_dba,date_insert,None])
                            conn2.commit()
                            cur2.close()
                            conn.close()
                        except Exception as e:
                            logging.error(f"Error insert Group Betting by IP to CTS DB: {e}")
                            message_telegram = f"Error insert Group Betting by IP to CTS DB: {e}"
                            SendLogTelegram.send_message(message_telegram)
                            raise ValueError
                
                cur.close()
                conn.close()
                
            except Exception as e:
                logging.error(f"Error insert Group Betting by IP to SPU DB: {e}")
                message_telegram = f"Error insert Group Betting by IP to SPU DB: {e}"
                SendLogTelegram.send_message(message_telegram)
                raise ValueError
            
            logging.info(f"Group Betting by IP is done, total: {time.time() - time_start} seconds")
            #message_telegram = f"Group Betting by IP is done, total {round((time.time() - time_start)/3600,4)} hours "
            #SendLogTelegram.send_message(message_telegram)
            #endregion
    except Exception as e:
        logging.error(f"Error at phase Group Betting by IP: {e}")
        message_telegram = f"Error at phase Group Betting by IP: {e}"
        SendLogTelegram.send_message(message_telegram)
        raise ValueError       
    

    