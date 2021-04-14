import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import json
import pandas as pd
import time
from app import config
from Utilities import FunctionSupport
from mysql.connector import MySQLConnection


def InsertAssociationSuspiciousInfo(batches_data):
    try:
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        for data in batches_data:
            json_obj2 = json.dumps(data)
            in1,out1 = cur.callproc('SPU_AIML_InsertAssociationSuspiciousInfo', [json_obj2, None])
            if out1 is not None:
                dataSP_error = json.loads(json_obj2)
                df_dataSP_error = pd.DataFrame(dataSP_error)
                df_dataSP_error.to_csv(config.errorFolder+f"file_error_SP_data_{time.time()}.csv",index=False)
                message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationSuspiciousInfo: {out1}'
                FunctionSupport.notify_logging(message_telegram)
            conn.commit()
        cur.close()
        conn.close()
    except Exception as err:
        message_telegram = f'{config.ENV} | Error insert AssociationSuspiciousInfo in SPU when day-end: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError