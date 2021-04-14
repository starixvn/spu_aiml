import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import json
from app import config
from Utilities import FunctionSupport
from mysql.connector import MySQLConnection

def InsertAssociationByAICTS(batches_data,date_insert):
    try:
        conn = MySQLConnection(user=config.ctsuser, password=config.ctspwd,
                            host=config.ctshost, port=config.ctsport, database=config.ctsdb)
        cur = conn.cursor()
        for data in batches_data:
            json_obj4 = json.dumps(data)
            in1,in2,out1 = cur.callproc('CTS_DC_Association_InsertAssociationByAI', [json_obj4, date_insert, None])
            if out1 is not None:
                message_telegram = f'{config.ENV} | Error return from SP CTS_DC_Association_InsertAssociationByAI: {out1} | With JSON {json_obj4}'
                FunctionSupport.notify_logging(message_telegram)
            conn.commit()
        cur.close()
        conn.close()
    except Exception as err:
        message_telegram = f'{config.ENV} | Error insert table byAI in DBA CTS when day-end: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError