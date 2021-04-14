import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from mysql.connector import MySQLConnection
from app import config
from Utilities import FunctionSupport


def InsertSystemParameter(date_insert):
    conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                           host=config.aimlhost, port=config.aimlport, database=config.aimldb)
    cur = conn.cursor()
    # update table SystemParameter
    in1, out1 = cur.callproc('SPU_AIML_UpdateScanStatus', [date_insert, None])
    if out1 is not None:
        message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_UpdateScanStatus: {out1}'
        FunctionSupport.notify_logging(message_telegram)
    conn.commit()

    cur.close()
    conn.close()
