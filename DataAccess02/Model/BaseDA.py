import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from mysql.connector import MySQLConnection
from Configuration.Configuration import config
from DataAccess02.Model.CommonDA import CommonDA
from Utilities import Utilities
class BaseDA(object):
        
    def execute(infoDB):
        connect_db = CommonDA(infoDB)
        try:
            infoDB.sp_output = connect_db.cursor.callproc(infoDB.sp,infoDB.param)
            if infoDB.sp_output[-1] != None:
                Utilities.notify_logging(infoDB.sp_mess)
            dba_results = [r.fetchall() for r in connect_db.cursor.stored_results()]
            connect_db.conn.commit()
            return dba_results
        except Exception as err:
            Utilities.notify_logging(infoDB.exception_mess +str(err))