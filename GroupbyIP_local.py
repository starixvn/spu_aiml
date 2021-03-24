import pandas as pd
import itertools
import time
import json
import os
import multiprocessing as mp
from tqdm import tqdm
import sys
import numpy as np
from mysql.connector import MySQLConnection
chunk_size = 5000
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
    if len(x) > 1:
        list_bettype = [i.split(',') for i in x]
        #print(list_bettype)
        result = list(itertools.chain.from_iterable(list_bettype))
        counts = len(result)
        result = set(result)
        return pd.Series((result,counts))
    else: 
        return None

def process_insertdba(chunk1,cur,conn):
    json_object1 = json.dumps(chunk1)
    cur.callproc('SPU_AIML.SPU_AIML_InsertCoupleIPStats',[json_object1,None])
    conn.commit()
if __name__ == '__main__':
    #sys.stdout = None
    data = pd.read_csv(r"D:\Project\Formula_BET\MatchData\bettrans_03_17_2021.csv",encoding='ISO-8859-1', skiprows=[1], skipfooter=1)
    
    #data = pd.read_csv(r"D:\Project\Formula_BET\MatchData\test_data\newdata.csv",encoding='ISO-8859-1')
    #print(data.info())
    #print("---------------------------------")
    timestart = time.time()
    df_dataip = data[['custid','ip','bettype','matchid','leagueid','homeid','awayid','transdate']]
    del data
    print(df_dataip.head(20))
    #data_ip['sample_id'] = data_ip['C1'].map(str) + data_ip['C2'].map(str)

    # prepare homeID, awayID, LeagueID, EventDate,
    starttime = time.time()
    df_prepareData = df_dataip.groupby('matchid')[['leagueid','homeid','awayid','transdate']].first()
    df_prepareData.reset_index(inplace=True)
    print(df_prepareData.head())
    print(time.time() - starttime)

    
    
    # get combination custid
    starttime = time.time()
    print("----------------")
    # df_cleancustid = df_dataip.groupby(['matchid','ip','custid']).first()
    # print(df_cleancustid.head())
    # df_cleancustid.reset_index(inplace=True)
    df_uniquebettye = df_dataip.groupby(['matchid','ip','bettype','custid']).first()
    df_uniquebettye.reset_index(inplace=True)
    print(df_uniquebettye.head())
    print('**********************')
    print(df_uniquebettye[(df_uniquebettye['custid'] == 46702609) & (df_uniquebettye['ip'] == "171.90.216.127") & (df_uniquebettye['matchid'] == 42223150)])
    print('**********************')
    print(df_uniquebettye[(df_uniquebettye['custid'] == 46702626) & (df_uniquebettye['ip'] == "171.90.216.127") & (df_uniquebettye['matchid'] == 42223150)])
    
    df_splitcustid = df_uniquebettye.groupby(['matchid','ip','bettype'])['custid'].agg(lambda x: list(itertools.combinations(x,2))).to_frame()
    #df_splitcustid = df_dataip.groupby(['matchid','ip','bettype'])['custid'].agg(lambda x: tuple(k for k,v in sorted(counts.items()))).to_frame()
    print(time.time() - starttime)
    # df_splitcustid.reset_index(inplace = True)
    # df_groupbyip.reset_index(inplace=True)
    
    
    print(df_splitcustid.head(20))
    #print(df_splitcustid.loc[[40435785]])
    print("------------------------------")
    
    #df_splitcustid.dropna(how='any',inplace=True)
    df_splitcustid['usersnumber'] = df_splitcustid['custid'].str.len()
    df_splitcustid = df_splitcustid[df_splitcustid['usersnumber'] >= 1]
    df_splitcustid.reset_index(inplace=True)
    #df_groupbyip.reset_index(inplace=True)
    
    
    starttime = time.time()
    print("----------------")
    print(df_splitcustid.head(20))
    df_splitcustid['custid'] = df_splitcustid['custid'].agg(lambda x: list(x))
    print(df_splitcustid.head(20))
    df_combicustid = pd.DataFrame(np.concatenate(df_splitcustid.custid), columns=['C1','C2']).reset_index(drop=True)
    df_combicustid['matchid'] = np.repeat(df_splitcustid.matchid.values, df_splitcustid['custid'].str.len())
    df_combicustid['ip'] = np.repeat(df_splitcustid.ip.values, df_splitcustid['custid'].str.len())
    df_combicustid['bettype'] = np.repeat(df_splitcustid.bettype.values, df_splitcustid['custid'].str.len())
    df_combicustid['sample_id'] = df_combicustid['C1'].map(str) + df_combicustid['C2'].map(str) + df_combicustid['matchid'].map(str)
    print(time.time() - starttime)
    print(df_combicustid.isnull().sum())
    print(df_combicustid.head())
    starttime = time.time()
    print("----------------")
    
    
    
    # list ip
    df_listAllIP = df_combicustid[['sample_id','ip']]
    df_listAllIP = transform_to_listIP(df_listAllIP)
    print(df_listAllIP.head())
    df_listAllIP['IPC'] = df_listAllIP['ip'].str.len()
    print(df_listAllIP.head())
    df_listAllIP['ip'] = [','.join(map(str, l)) for l in df_listAllIP['ip']]
    df_listAllIP.set_index('sample_id',inplace=True)
    print(time.time() - starttime)
    print(df_listAllIP.head())
    
    # count bettype with different ip
    
    
    # list bettype
    df_listAllBettype = df_combicustid[['sample_id','bettype']]
    df_listAllBettype = transform_to_listBettype(df_listAllBettype)
    
    
    #df_listAllBettype['15'] = list(map(set,df_listAllBettype['bettype'].values))
    print(df_listAllBettype.head())
    #df_listAllBettype['bettype'] = df_listAllBettype['bettype'].apply(lambda x: get_unique_bettype(x))
    #df_listAllBettype[['bettype','BTC']] = df_listAllBettype['bettype'].apply(lambda x: get_unique_bettype(x))
    df_listAllBettype['BTC'] = df_listAllBettype['bettype'].str.len()
    df_listAllBettype['bettype'] = df_listAllBettype['bettype'].apply(lambda x: set(x))
    #print(df_listAllBettype.head(20))
    df_listAllBettype['bettype'] = [','.join(map(str, l)) for l in df_listAllBettype['bettype']]
    df_listAllBettype.set_index('sample_id',inplace=True)
    print(df_listAllBettype.head(20))
    # take unique row
    df_combicustid = df_combicustid.groupby('sample_id').first()
    df_combicustid['ip'] = df_listAllIP['ip']
    df_combicustid['IPC'] = df_listAllIP['IPC']
    df_combicustid['bettype'] = df_listAllBettype['bettype']
    
    df_combicustid['BTC'] = df_listAllBettype['BTC']
    
    #final result
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
    print("-----------")
    #print(df_groupbyip.head(20))
    print("--------------")
    
    print(df_combicustid.head(20))
    print("--------------")
    #df_result2 = df_result[df_result['C1'] != df_result['C2']]
    #print(df_result2)
    print('------------------')
    print(df_result.head(20))
    #print(df_result.info())
    #fulldata_dba = df_result.to_json(orient="records")
    #df_result.to_csv(r"D:\Project\Formula_BET\MatchData\test_data\datainsert_groupip.csv",index=False)
    fullDataIPSPU_dba = df_result.to_dict(orient="records")
    chunks1 = [fullDataIPSPU_dba[x:x+chunk_size]
                for x in range(0, len(fullDataIPSPU_dba), chunk_size)]
    
    
    #print(fulldata_dba)
    #print(fulldata_dba)
    try:
        conn = MySQLConnection(user = 'darius.vn', password = '1qaz@Wsx3edc', host = '10.18.200.70', port = '3307', database = 'SPU_AIML')
        cur = conn.cursor()
        for chunk1 in chunks1:
            json_object1 = json.dumps(chunk1)
            #print ("Estimated size: " + str(sys.getsizeof(json_object1) / 1024) + "KB")
            
            
            cur.callproc('SPU_AIML.SPU_AIML_InsertCoupleIPStats',[json_object1,None])
            dba_results = [r.fetchall() for r in cur.stored_results()]
            conn.commit()
            # if len(dba_results[0]) == 0:
            #     continue
            # df = pd.DataFrame(dba_results[0], columns=[
            # "C1",
            # "C2"])
            # fullDataIPCTS_dba = df.to_csv(orient="records")
            # conn2 = MySQLConnection(user = 'darius.vn', password = '1qaz@Wsx3edc', host = '10.18.200.70', port = '3307', database = 'CTS_DataCenter')
            # cur2 = conn2.cursor()
            # #CTS_DataCenter.CTS_DC_Association_InsertAssociationByIP ('[{"C1": 43600693, "C2": 45}]', '2021-01-11', @ErrorMessage)
            
        
        cur.close()
        conn.close()

    except Exception as err:
        print(err)
    # # #print(dba_results)
    # df = pd.DataFrame(dba_results[0], columns=[
    #         "C1",
    #         "C2"])
    # #print(df.head())