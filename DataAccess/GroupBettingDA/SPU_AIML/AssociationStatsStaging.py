import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import json
from mysql.connector import MySQLConnection
from app import config
from Utilities import FunctionSupport

def TruncateAssociationStatsStaging():
    try:
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        # Truncate table AssociationStatsStaging
        cur.callproc('SPU_AIML_DBA_Truncate_Table',
                    ['AssociationStatsStaging'])
        conn.commit()
    except Exception as e:
        message_telegram = f"{config.ENV} | Error at Truncate table AssociationStatsStaging: {e}"
        FunctionSupport.notify_logging(message_telegram)
        
def GetAssociationStatsStaging(custid_list):
    try:
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        in1,out1 = cur.callproc('SPU_AIML_GetAssociationStatsStaging',[custid_list, None])
        if out1 is not None:
            message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_GetAssociationStatsStaging: {out1} | With CusList {custid_list}'
            FunctionSupport.notify_logging(message_telegram)
        dba_results = [r.fetchall() for r in cur.stored_results()]
        conn.commit()
        cur.close()
        conn.close()
        return dba_results
    except Exception as err:
        message_telegram = f'{config.ENV} | Error get data from AssociationStatsStaging in SPU when on-the-fly: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError
    
def UpdateAssociationStatsStagingStatus(custid_list):
    try:
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                            host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cur = conn.cursor()
        #cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [
                    #int(args[0]), int(args[1]), None])
        in1,out1 = cur.callproc('SPU_AIML_UpdateAssociationStatsStagingStatus', [custid_list, None])
        if out1 is not None:
            message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_UpdateAssociationStatsStagingStatus: {out1} | With CusList {custid_list}'
            FunctionSupport.notify_logging(message_telegram)
        conn.commit()

        cur.close()
        conn.close()

    except Exception as err:
        message_telegram = f'{config.ENV} | Error Update Staging Status: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError
    
def InsertAssociationStatsStaging(batches_data):
    try:
        conn = MySQLConnection(user=config.aimluser, password=config.aimlpwd,
                                host=config.aimlhost, port=config.aimlport, database=config.aimldb)
        cursor = conn.cursor()
        for data in batches_data:
            jsonList = json.dumps(data)
            in_, out1 = cursor.callproc('SPU_AIML_InsertAssociationStatsStaging', [jsonList, None])
            if out1 is not None:
                message_telegram = f'{config.ENV} | Error return from SP SPU_AIML_InsertAssociationStatsStaging: {out1} | With JSON {jsonList}'
                FunctionSupport.notify_logging(message_telegram)
            conn.commit()
        cursor.close()
        conn.close()
    except Exception as err:
        message_telegram = f'{config.ENV} | Error insert table AssociationStatsStaging in SPU DB: {err}'
        FunctionSupport.notify_logging(message_telegram)
        raise ValueError
    
