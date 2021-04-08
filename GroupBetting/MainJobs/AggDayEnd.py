import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from GroupBetting.Support import helper
from GroupBetting.Support import Function_Support
from mysql.connector import MySQLConnection
import time
import os
import json
import pandas as pd
import logging
def day_end_aggregate(args):
    try:
        config = args[2]
        date_insert = args[3]
        the_first_is_the_last = args[4]
        daily_cus_dict = args[5]
        time_getStaging = time.time()
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                    host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        in1,in2,out1 = cur.callproc('SPU_AIML_GetAssociationStats',[int(args[0]), int(args[1]), None])
        if out1 is not None:
            message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_GetAssociationStats: {out1} | FROM {int(args[0])} TO {int(args[1])}'
            Function_Support.notify_logging(message_telegram)
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
            lambda z: Function_Support.count_joining_combs_by_daily_cus_dict(z['C1'], z['C2'],daily_cus_dict), axis=1)
        
        df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
        
        df = df.astype({"sample_id": 'int64'})
        df['TS'] = df['TS'].astype('float')
        df['AccTS'] = df['AccTS'].astype('float')
        df['AccMS'] = df['AccMS'].astype('float')
        df['AccLS'] = df['AccLS'].astype('float')

        df_byAI,df_byAISPU,df_resultinfo,isTraceLog,df_result3 = Function_Support.GroupBetting_FeatureScore(df,config,the_first_is_the_last,True)
        
        # move to dba
        fulldatabyAI_dba = df_byAI.to_dict(orient="records")
        fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")
        fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
        
        chunks2 = [fulldatainfo_dba[x:x+config.chunk_size]
                for x in range(0, len(fulldatainfo_dba), config.chunk_size)]
        chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]   

        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            if isTraceLog:
                for chunk5 in chunks5:
                    json_obj5 = json.dumps(chunk5)
                    in1,out1 = cur.callproc('SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                    if out1 is not None:
                        message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1} | With JSON {json_obj5}'
                        Function_Support.notify_logging(message_telegram)
                    conn.commit()
                    
            if the_first_is_the_last:
                for chunk2 in chunks2:
                    json_obj2 = json.dumps(chunk2)
                    in1,out1 = cur.callproc('SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
                    if out1 is not None:
                        dataSP_error = json.loads(json_obj2)
                        df_dataSP_error = pd.DataFrame(dataSP_error)
                        df_dataSP_error.to_csv(config.errorFolder+f"file_error_SP_data_{time.time()}.csv",index=False)
                        message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}'
                        Function_Support.notify_logging(message_telegram)
                    conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            message_telegram = f'{config.ENV} | Error insert 3 table in DBA when day-end: {err}'
            Function_Support.notify_logging(message_telegram)
            raise ValueError

        # insert dba CTS
        if config.transfer_score:
            try:
                conn = MySQLConnection(user=config.ctsuser, password=config.ctspwd,
                                    host=config.ctshost, port=config.ctsport, database=config.ctsdb)
                cur = conn.cursor()
                for chunk4 in chunks4:
                    json_obj4 = json.dumps(chunk4)
                    in1,in2,out1 = cur.callproc('CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
                    if out1 is not None:
                        message_telegram = f'{config.ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1} | With JSON {json_obj4}'
                        Function_Support.notify_logging(message_telegram)
                    conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                message_telegram = f'{config.ENV} | Error insert table byAI in DBA CTS when day-end: {err}'
                Function_Support.notify_logging(message_telegram)
                raise ValueError
        
        # Compute accomulatedly
        df_sampleDailyScore = df[['sample_id', 'C1',
                                  'C2', 'AccTS', 'AccMS', 'AccLS', 'AccTJD', 'AccTJSC']]
        df_DailyScore = df_sampleDailyScore.groupby('sample_id').first()

        #df_result3.set_index('sample_id',inplace=True)
        df_DailyScore = pd.merge(df_DailyScore,df_result3[['TS','MS','LS','TJC','TJSC','BC']],left_index=True, right_index=True)

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

        
        df_byAISample03 = df_DailyScore[['C1', 'C2', 'S','AccTJSC']]
        df_byAISample03.rename(columns={'AccTJSC':'TJSC'},inplace=True)
        df_byAI = df_byAISample03[(df_byAISample03['S'] >= config.percent_score) & (
            df_byAISample03['TJSC'] >= config.combination_threshold)]
                
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


        chunks1 = [fulldata_dba[x:x+config.chunk_size]
                for x in range(0, len(fulldata_dba), config.chunk_size)]

        chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

        chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]   

        try:
            conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
            cur = conn.cursor()
            if isTraceLog:
                for chunk5 in chunks5:
                    json_obj5 = json.dumps(chunk5)
                    in1,out1 = cur.callproc('SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                    if out1 is not None:
                        message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1} | With JSON {json_obj5}'
                        Function_Support.notify_logging(message_telegram)
                    conn.commit()
                    
            for chunk1 in chunks1:
                json_obj1 = json.dumps(chunk1)
                in1,in2,out1 = cur.callproc('SPU_AIML_InsertAssociationStats', [json_obj1, date_insert, None])
                if out1 is not None:
                    message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationStats: {out1} | With JSON {json_obj1}'
                    Function_Support.notify_logging(message_telegram)
                conn.commit()

            cur.close()
            conn.close()

        except Exception as err:
            message_telegram = f'{config.ENV} | Error insert 3 table in DBA when Acc day-end: {err}'
            Function_Support.notify_logging(message_telegram)
            raise ValueError

        # insert dba CTS
        if config.transfer_score:
            try:
                conn = MySQLConnection(user=config.ctsuser, password=config.ctspwd,
                                    host=config.ctshost, port=config.ctsport, database=config.ctsdb)
                cur = conn.cursor()
                for chunk4 in chunks4:
                    json_obj4 = json.dumps(chunk4)
                    in1,in2,out1 = cur.callproc('CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
                    if out1 is not None:
                        message_telegram = f'{config.ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1} | With JSON {json_obj4}'
                        Function_Support.notify_logging(message_telegram)
                    conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                message_telegram = f'{config.ENV} | Error insert table byAI in DBA CTS when Acc day-end: {err}'
                Function_Support.notify_logging(message_telegram)
                raise ValueError
        logging.info(f"Time to complete child process into phase Acc day-end {os.getpid()}: {time.time() - time_getStaging}")
    except Exception as err:
        message_telegram = f'{config.ENV} | Error in day-end agg function: {err}'
        Function_Support.notify_logging(message_telegram)
        raise ValueError