import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import json
from app import config
from Utilities import FunctionSupport
from mysql.connector import MySQLConnection


def InsertAssociationByAISPU(batches_data):
    try:
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        for data in batches_data:
            json_obj5 = json.dumps(data)
            in1,out1 = cur.callproc('SPU_AIML_InsertAssociationByAI', [json_obj5, None])
            if out1 is not None:
                message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationByAI: {out1} | With JSON {json_obj5}'
                FunctionSupport.notify_logging(message_telegram)
            conn.commit()
        cur.close()
        conn.close()
    except Exception as err:
        message_telegram = f'{config.ENV} | Error insert AssociationByAI in SPU when day-end: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError