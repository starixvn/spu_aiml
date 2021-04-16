import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from TaskManagement.GroupBettingManagement.GroupBettingController import config
from Utilities import FunctionSupport
from mysql.connector import MySQLConnection


def InsertAssociationByIPCTS(batch_data,date_insert):
    try:
        conn = MySQLConnection(user=config.ctsuser, password=config.ctspwd,
            host=config.ctshost, port=config.ctsport, database=config.ctsdb)
        cur = conn.cursor()
        in1,in2,out1 = cur.callproc('CTS_DC_Association_InsertAssociationByIP',[batch_data,date_insert,None])
        if out1 is not None:
            message_telegram = f'{config.ENV} | Error return from SP CTS_DC_Association_InsertAssociationByIP: {out1}'
            FunctionSupport.notify_logging(message_telegram)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        message_telegram = f"{config.ENV} | Error insert Group Betting by IP to CTS DB: {e}"
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError