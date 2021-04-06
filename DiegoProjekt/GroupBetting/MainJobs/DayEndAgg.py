import sys
sys.path.append('C:/Users/diego.nguyen/diegoProj/GroupBetting')
import json
import pandas as pd
import numpy as np
from mysql.connector import MySQLConnection
from Configuration.LocalConfiguration import LocalConfiguration
from Configuration.ProConfiguration import ProConfiguration
from Supporters.Helpers import count_joining_combs
from Supporters.Aggregate import aggregate
ENV='LOCAL'

if ENV=='LOCAL':

    config = LocalConfiguration()

else:
    config = ProConfiguration()

aimluser=config.getSPU_AIMLUsername(config)
aimlpwd=config.getSPU_AIMLPassword(config)
aimlhost=config.getSPU_AIMLHost(config)
aimlport=config.getSPU_AIMLPort(config)
aimldb=config.getSPU_AIMLDatabaseName(config)

ctsuser=config.getCTS_DataCenterUsername(config)
ctspwd=config.getCTS_DataCenterPassword(config)
ctshost=config.getCTS_DataCenterHost(config)
ctsport=config.getCTS_DataCenterPort(config)
ctsdb=config.getCTS_DataCenterDatabaseName(config)

chunk_size = int(config.getChunkSize(config))
transfer_score = config.getTransferDataScore(config)
percent_score = int(config.getPercentScore(config))
combination_threshold = int(config.GetCombinationThreshold(config))

def DayEndAgg(args):
    """
    >>> Input   :   MinCustID               : integer
                    MaxCustID               : integer
                    date_insert             : string | format : YYYY-MM-DD
                    daily_cus_dict          : dictionary
                    the_first_is_the_last   : boolean
    """
    try:
        date_insert,daily_cus_dict,the_first_is_the_last=args[2],args[3],args[4]
        # sub_results=results[(results.C1>=int(args[0]))&(results.C1<=int(args[1]))]
        conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
        cur = conn.cursor()
        cur.callproc('SPU_AIML_GetAssociationStats',
                    [int(args[0]), int(args[1]), None])
        dba_results = [r.fetchall() for r in cur.stored_results()]
        conn.commit()
        cur.close()
        conn.close()

        if len(dba_results[0]) == 0:
            return True
        df = pd.DataFrame(dba_results[0], columns=[
            "C1"
            ,"C2"
            ,"TS"
            ,"ML"
            ,"BL"
            ,"LeagueID"
            ,"IsMajorLeague"
            ,"TJC"
            ,"IsNew"
            ,"AccTS"
            ,"AccMS"
            ,"AccLS"
            ,"AccTJD"
            ,"AccTJSC"
            ])
        # fill 0 to NaN
        df['AccTS'].fillna(0, inplace=True)
        df['AccMS'].fillna(0, inplace=True)
        df['AccLS'].fillna(0, inplace=True)
        df['AccTJD'].fillna(0, inplace=True)
        df['AccTJSC'].fillna(0, inplace=True)

        df['TJC'] = df.apply(
            lambda z: count_joining_combs(z['C1'], z['C2'],daily_cus_dict), axis=1)
        
        df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
        
        df = df.astype({"sample_id": 'int64'})
        df['TS'] = df['TS'].astype('float')
        df['AccTS'] = df['AccTS'].astype('float')
        df['AccMS'] = df['AccMS'].astype('float')
        df['AccLS'] = df['AccLS'].astype('float')
        
        BuchOfDataFrames = aggregate(df,'DayEnd',the_first_is_the_last)
        if the_first_is_the_last:
            df_result3,df_resultinfo,df_byAI,df_byAISPU,isTraceLog = BuchOfDataFrames
            fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
            chunks2 = [fulldatainfo_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatainfo_dba), chunk_size)]
        else:
            df_result3,df_byAI,df_byAISPU,isTraceLog = BuchOfDataFrames
        # move to dba
        # fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")
        fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")


        chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]   

        try:
            conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                host=aimlhost, port=aimlport, database=aimldb)
            cur = conn.cursor()
            if isTraceLog:
                for chunk5 in chunks5:

                    json_obj5 = json.dumps(chunk5)
                    # cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [
                    #                 json_obj5, None])
                    in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                    if out1 is not None:
                        print(out1)
                        # logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}')
                        # message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}'
                        # SendLogTelegram.send_message(message_telegram)
                    conn.commit()
                    
            if the_first_is_the_last:
                for chunk2 in chunks2:
                    json_obj2 = json.dumps(chunk2)
                    in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
                    if out1 is not None:
                        print(out1)
                    conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            # logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
            print(f'{ENV} | Error insert 3 table in DBA: {err}')
            # message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError

        # insert dba CTS
        if transfer_score:
            try:
                conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                    host=ctshost, port=ctsport, database=ctsdb)
                cur = conn.cursor()
                for chunk4 in chunks4:
                    json_obj4 = json.dumps(chunk4)
                    # cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [
                    #             json_obj4, date_insert, None])
                    in1,in2,out1 = cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
                    if out1 is not None:
                        print(out1)
                        # logging.error(f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}')
                        # message_telegram = f'{ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1}'
                        # SendLogTelegram.send_message(message_telegram)
                    conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                # logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                print(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
        
        # Compute accomulatedly
        df_sampleDailyScore = df[['sample_id', 'C1',
                                  'C2', 'AccTS', 'AccMS', 'AccLS', 'AccTJD', 'AccTJSC']]
        df_DailyScore = df_sampleDailyScore.groupby('sample_id').first()

        
        # print('df_result3',df_result3.head(),sep='\n')
        # df_result3.set_index('sample_id',inplace=True)
        df_DailyScore = pd.merge(df_DailyScore,df_result3[['TS','MS','LS','TJC','TJSC','BC']],left_index=True, right_index=True)
        # print('df_DailyScore',df_DailyScore.head(),sep='\n')
        df_DailyScore['AccTS'] = df_DailyScore['AccTS'] + df_DailyScore['TS']

        df_DailyScore['AccMS'] = df_DailyScore['AccMS'] + df_DailyScore['MS']

        df_DailyScore['AccLS'] = df_DailyScore['AccLS'] + df_DailyScore['LS']

        df_DailyScore['AccTJSC'] = df_DailyScore['AccTJSC'] + df_DailyScore['TJSC']
    
        df_DailyScore['AccTJD'] += 1
        
        # aggregate with history data
        df_DailyScore['S'] = 100 * (df_DailyScore['AccTS'] + df_DailyScore['AccMS'] +
                                    df_DailyScore['AccLS']) / (3*df_DailyScore['AccTJD'])

        df_DailyScore = df_DailyScore.drop(columns=['TS','MS','LS'])

        df_DailyScore.rename(columns={'AccTS':'TS','AccMS':'MS','AccLS':'LS','AccTJD':'TJD'},inplace=True)

        # print()
        
        df_byAISample03 = df_DailyScore[['C1', 'C2', 'S','AccTJSC']]
        df_byAISample03.rename(columns={'AccTJSC':'TJSC'},inplace=True)
        df_byAI = df_byAISample03[(df_byAISample03['S'] >= percent_score) & (
            df_byAISample03['TJSC'] >= combination_threshold)]
                
        isTraceLog = False
        df_byAISPU = pd.DataFrame()
        if len(df_byAI.index) != 0:
            isTraceLog = True
            df_result4 = df_DailyScore[['TS', 'MS', 'LS', 'TJD', 'TJC']]
            df_byAISPU = pd.merge(df_result4, df_byAI,
                                left_index=True, right_index=True)

        # move to dba
        fulldata_dba = df_DailyScore.to_dict(orient="records")
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")
        fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")


        chunks1 = [fulldata_dba[x:x+chunk_size]
                for x in range(0, len(fulldata_dba), chunk_size)]

        chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                for x in range(0, len(fulldatabyAI_dba), chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
                for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]   

        try:
            conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                host=aimlhost, port=aimlport, database=aimldb)
            cur = conn.cursor()
            if isTraceLog:
                for chunk5 in chunks5:

                    json_obj5 = json.dumps(chunk5)
                    # cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [
                    #                 json_obj5, None])
                    in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                    if out1 is not None:
                        print(out1)
                        # logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}')
                        # message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}'
                        # SendLogTelegram.send_message(message_telegram)
                    conn.commit()
            for chunk1 in chunks1:
                json_obj1 = json.dumps(chunk1)
                in1,in2,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationStats', [json_obj1, date_insert, None])
                if out1 is not None:
                    print(out1)
                conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            # logging.error(f'{ENV} | Error insert 3 table in DBA: {err}')
            print(f'{ENV} | Error insert 3 table in DBA: {err}')
            # message_telegram = f'{ENV} | Error insert 3 table in DBA: {err}'
            # SendLogTelegram.send_message(message_telegram)
            raise ValueError

        # insert dba CTS
        if transfer_score:
            try:
                conn = MySQLConnection(user=ctsuser, password=ctspwd,
                                    host=ctshost, port=ctsport, database=ctsdb)
                cur = conn.cursor()
                for chunk4 in chunks4:
                    json_obj4 = json.dumps(chunk4)
                    in1,in2,out1 = cur.callproc('CTS_DataCenter.CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
                    if out1 is not None:
                        print(out1)
                    conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                # logging.error(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                print(f'{ENV} | Error insert table byAI in DBA CTS: {err}')
                # message_telegram = f'{ENV} | Error insert table byAI in DBA CTS: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
    except Exception as err:
        # logging.error(f'{ENV} | Error in day-end agg function: {err}')
        print(f'{ENV} | Error in day-end agg function: {err}')
        # message_telegram = f'{ENV} | Error in day-end agg function: {err}'
        # SendLogTelegram.send_message(message_telegram)
        raise ValueError