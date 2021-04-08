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
def aggregate(args):
    try:
        config = args[1]
        date_insert = args[2]
        daily_cus_dict = args[3]
        time_getStaging = time.time()
        # date_insert,daily_cus_dict=args[2],args[3]
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                            host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        in1,out1 = cur.callproc('SPU_AIML_GetAssociationStatsStaging',[args[0], None])
        if out1 is not None:
            message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1} | With CusList {args}'
            Function_Support.notify_logging(message_telegram)
        dba_results = [r.fetchall() for r in cur.stored_results()]
        conn.commit()
        cur.close()
        conn.close()
        if len(dba_results[0]) == 0:
            return []
        df = pd.DataFrame(dba_results[0], columns=[
            "C1",
            "C2",
            "TS",
            "ML",
            "BL",
            "LeagueID",
            "IsMajorLeague",
            "TJC",
            "IsNew"
            ])
        IsNewdf=df[df.IsNew==1]
        #logging.info(f"Time get data from StatStaging: {time.time() - time_getStaging}")
        if len(IsNewdf)>0:
            time_newBatch = time.time()
            IsNewdf['sample_id'] = IsNewdf['C1'].map(str) + IsNewdf['C2'].map(str)
            IsNewdf = IsNewdf.astype({"sample_id": 'int64'})
            IsNewdf['TS'] = IsNewdf['TS'].astype('float')
            
            df_byAI,df_byAISPU,df_resultinfo,isTraceLog = Function_Support.GroupBetting_FeatureScore(df,config,True)
            
            # move to dba
            fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")


            chunks2 = [fulldatainfo_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatainfo_dba), config.chunk_size)]


            chunks4 = [fulldatabyAI_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), config.chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+config.chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), config.chunk_size)]
            #logging.info(f"Time to calculate new batch: {time.time() - time_newBatch}")
            time_inserttable = time.time()
            try:
                conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                    host=config.aimlhost, port=config.aimlport, database=config.aimldb)
                cur = conn.cursor()
                if isTraceLog:
                    # for (chunk2, chunk5) in zip(chunks2, chunks5):
                    for chunk5 in chunks5:
                        json_obj5 = json.dumps(chunk5)
                        in1,out1 = cur.callproc('SPU_AIML_InsertAssociationByAI', [json_obj5, None])
                        if out1 is not None:
                            message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1}'
                            Function_Support.notify_logging(message_telegram)
                        conn.commit()
                # else:
                for chunk2 in chunks2:
                    json_obj2 = json.dumps(chunk2)
                    in1,out1 = cur.callproc('SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
                    if out1 is not None:
                        print(out1)
                        dataSP_error = json.loads(json_obj2)
                        df_dataSP_error = pd.DataFrame(dataSP_error)
                        df_dataSP_error.to_csv(config.errorFolder+f"file_error_SP_data_{time.time()}.csv",index=False)
                        message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1} | With JSON {json_obj2}'
                        Function_Support.notify_logging(message_telegram)
                    conn.commit()
                cur.close()
                conn.close()
            except Exception as err:
                message_telegram = f'{config.ENV} | Error insert 3 table in DBA: {err}'
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
                            message_telegram = f'{config.ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1} With JSON {json_obj4}'
                            Function_Support.notify_logging(message_telegram)
                        conn.commit()

                    cur.close()
                    conn.close()

                except Exception as err:
                    message_telegram = f'{config.ENV} | Error insert table byAI in DBA CTS: {err}'
                    Function_Support.notify_logging(message_telegram)
                    raise ValueError
            
            # update Staging Status
            try:
                conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                    host=config.aimlhost, port=config.aimlport, database=config.aimldb)
                cur = conn.cursor()
                #cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [
                            #int(args[0]), int(args[1]), None])
                in1,out1 = cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [args, None])
                if out1 is not None:
                    message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_UpdateAssociationStatsStagingStatus: {out1} | With CusList {args}'
                    Function_Support.notify_logging(message_telegram)
                conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                message_telegram = f'{config.ENV} | Error Update Staging Status: {err}'
                Function_Support.notify_logging(message_telegram)
                raise ValueError
            #logging.info(f"Time to insert all table in DB: {time.time() - time_inserttable}")
        if len(df)>len(IsNewdf):
            time_onthefly = time.time()
            df['TJC']=df.apply(lambda z : Function_Support.count_joining_combs_by_daily_cus_dict(z['C1'],z['C2'],daily_cus_dict),axis=1)
            df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
            df = df.astype({"sample_id": 'int64'})
            df['TS'] = df['TS'].astype('float')
            
            df_byAI,df_byAISPU,df_resultinfo,isTraceLog = Function_Support.GroupBetting_FeatureScore(df,config)
            
            # move to dba
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")

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
                cur.close()
                conn.close()
            except Exception as err:
                message_telegram = f'{config.ENV} | Error insert Assocication By AI at phase On The Fly: {err}'
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
                    message_telegram = f'{config.ENV} | Error insert table byAI in DBA CTS: {err}'
                    Function_Support.notify_logging(message_telegram)
                    raise ValueError
        logging.info(f"Time to complete child process {os.getpid()}: {time.time() - time_getStaging}")
        

    except Exception as err:
        message_telegram = f'{config.ENV} | Error in agg function: {err}'
        Function_Support.notify_logging(message_telegram)
        raise ValueError