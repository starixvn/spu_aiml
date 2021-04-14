import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import json
import pandas as pd
import logging
from DataAccess.AssociationIPDA.CTS_DataCenter import AssociationByIPCTS
from app import config
from Utilities import FunctionSupport
from mysql.connector import MySQLConnection


def InsertCoupleIPStats(batches_data,date_insert):
    try:
        
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                    host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        for data in batches_data:
            json_objIP1 = json.dumps(data)
            in1,out1 = cur.callproc('SPU_AIML_InsertCoupleIPStats',[json_objIP1,None])
            if out1 is not None:
                message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertCoupleIPStats: {out1}'
                FunctionSupport.notify_logging(message_telegram)     
            dba_results = [r.fetchall() for r in cur.stored_results()]
            conn.commit()
            if config.transfer_ip:
                if len(dba_results[0]) > 0:
                    df_CTS = pd.DataFrame(dba_results[0], columns=[
                    "C1",
                    "C2"])
                    fullDataIPCTS_dba = df_CTS.to_json(orient="records")
                    AssociationByIPCTS.InsertAssociationByIPCTS(fullDataIPCTS_dba,date_insert)
        cur.close()
        conn.close()
    except Exception as err:
        message_telegram = f"{config.ENV} | Error insert CoupleIPStats to SPU DB: {err}"
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError