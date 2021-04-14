import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import json
from app import config
from Utilities import FunctionSupport
from mysql.connector import MySQLConnection


def GetAssociationStats(from_custid,to_custid):
    try:
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                            host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        in1, in2, out1 = cur.callproc('SPU_AIML_GetAssociationStats', [
                                    from_custid, to_custid, None])
        if out1 is not None:
            message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_GetAssociationStats: {out1} | FROM {from_custid} TO {to_custid}'
            FunctionSupport.notify_logging(message_telegram)
        dba_results = [r.fetchall() for r in cur.stored_results()]
        conn.commit()
        cur.close()
        conn.close()
        return dba_results
    except Exception as err:
        message_telegram = f'{config.ENV} | Error get data from AssociationStats when day-end: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError
    
def InsertAssociationStats(batches_data,date_insert):
    try:
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        for data in batches_data:
            json_obj1 = json.dumps(data)
            in1,in2,out1 = cur.callproc('SPU_AIML_InsertAssociationStats', [json_obj1, date_insert, None])
            if out1 is not None:
                message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationStats: {out1} | With JSON {json_obj1}'
                FunctionSupport.notify_logging(message_telegram)
            conn.commit()
        cur.close()
        conn.close()
    except Exception as err:
        message_telegram = f'{config.ENV} | Error insert AssociationStats in SPU when day-end: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError
