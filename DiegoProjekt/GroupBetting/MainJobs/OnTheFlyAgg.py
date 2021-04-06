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
chunk_size = int(config.getChunkSize(config))

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

transfer_score = config.getTransferDataScore(config)

def OnTheFlyAgg(args):
    """
    >>> Input   :   customer list   : string
                    date_insert     : string | format : YYYY-MM-DD
                    daily_cus_dict  : dictionary     
    """
    try:
        # date_insert,daily_cus_dict=args[2],args[3]
        date_insert,daily_cus_dict=args[1],args[2]
        conn = MySQLConnection(user=aimluser, password=aimlpwd,
                            host=aimlhost, port=aimlport, database=aimldb)
        cur = conn.cursor()
        # cur.callproc('SPU_AIML_GetAssociationStatsStaging',
        #             [int(args[0]), int(args[1]), None])
        # cur.callproc('SPU_AIML_GetAssociationStatsStaging',
        #             [args[0], None])
        in1,out1 = cur.callproc('SPU_AIML_GetAssociationStatsStaging',[args[0], None])
        if out1 is not None:
            print(out1)
            # logging.error(f'{ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1}')
            # message_telegram = f'{ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1}'
            # SendLogTelegram.send_message(message_telegram)
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
        # print('df',df.head(),sep='\n')
        df['sample_id'] = df['C1'].map(str) + df['C2'].map(str)
        df = df.astype({"sample_id": 'int64'})
        df['TS'] = df['TS'].astype('float')
        IsNewdf=df[df.IsNew==1]
        if len(IsNewdf)>0:
            
            df_resultinfo,df_byAI,df_byAISPU,isTraceLog = aggregate(IsNewdf,'NewData')
            # move to dba
            fulldatainfo_dba = df_resultinfo.to_dict(orient="records")
            fulldatabyAI_dba = df_byAI.to_dict(orient="records")
            fulldatabyAISPU_dba = df_byAISPU.to_dict(orient="records")


            chunks2 = [fulldatainfo_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatainfo_dba), chunk_size)]


            chunks4 = [fulldatabyAI_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAI_dba), chunk_size)]

            chunks5 = [fulldatabyAISPU_dba[x:x+chunk_size]
                    for x in range(0, len(fulldatabyAISPU_dba), chunk_size)]
            
            try:
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                if isTraceLog:
                    for (chunk2, chunk5) in zip(chunks2, chunks5):

                        json_obj2 = json.dumps(chunk2)
                        # cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
                        #             json_obj2, None])
                        in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
                        if out1 is not None:
                            print(out1)
                            # logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}')
                            # message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}'
                            # SendLogTelegram.send_message(message_telegram)
                        conn.commit()
                        
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
                else:
                    for chunk2 in chunks2:
                        json_obj2 = json.dumps(chunk2)
                        # cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [
                        #             json_obj2, None])
                        in1,out1 = cur.callproc('SPU_AIML.SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
                        if out1 is not None:
                            print(out1)
                            # logging.error(f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}')
                            # message_telegram = f'{ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}'
                            # SendLogTelegram.send_message(message_telegram)
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
            
            # update Staging Status
            try:
                conn = MySQLConnection(user=aimluser, password=aimlpwd,
                                    host=aimlhost, port=aimlport, database=aimldb)
                cur = conn.cursor()
                # cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [
                #             args[0], None])
                in1,out1 = cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [args[0], None])
                if out1 is not None:
                    print(out1)
                    # logging.error(f'{ENV} | Error return from SP SPU_AIML_UpdateAssociationStatsStagingStatus: {out1}')
                    # message_telegram = f'{ENV} | Error return from SP SPU_AIML_UpdateAssociationStatsStagingStatus: {out1}'
                    # SendLogTelegram.send_message(message_telegram)
                conn.commit()

                cur.close()
                conn.close()

            except Exception as err:
                # logging.error(f'{ENV} | Error Update Staging Status: {err}')
                print(f'{ENV} | Error Update Staging Status: {err}')
                # message_telegram = f'{ENV} | Error Update Staging Status: {err}'
                # SendLogTelegram.send_message(message_telegram)
                raise ValueError
        if len(df)>len(IsNewdf):
            df['TJC']=df.apply(lambda z : count_joining_combs(z['C1'],z['C2'],daily_cus_dict),axis=1)
            df_byAI,df_byAISPU,isTraceLog = aggregate(df,'OnTheFly')
            # move to dba
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
                cur.close()
                conn.close()
            except Exception as err:
                # logging.error(f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}')
                print(f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}')
                # message_telegram = f'{ENV} | Error insert Assocication By AI at phase On The Fly: {err}'
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
        
        # return df_result3.to_dict(orient='records')

    except Exception as err:
        # logging.error(f'{ENV} | Error in agg function: {err}')
        print(f'{ENV} | Error in agg function: {err}')
        # message_telegram = f'{ENV} | Error in agg function: {err}'
        # SendLogTelegram.send_message(message_telegram)
        raise ValueError