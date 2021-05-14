import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
# sys.path.append("D:\\Project\\aiml_cleancode\\")
from Configuration.Configuration import config
from DataAccess.CoreDA.CommonDA import CommonDA
from mysql.connector.pooling import MySQLConnectionPool
from Utilities import Utilities


class BaseDA(object):
    def call_sp(info_db,connection):
        try:
            sp_output = connection.cursor.callproc(info_db.sp, info_db.param())
            if sp_output[-1] != None:
                Utilities.notify_logging(
                    info_db.output_sperror_msg + str(sp_output))
            dba_results = [r.fetchall() for r in connection.cursor.stored_results()]
            #connection.conn.commit()
            return dba_results
        except Exception as err:
            Utilities.notify_logging(info_db.output_exception_msg + str(err))
            raise ValueError(err)

    def execute(name_sp, info_db, param,connection):
        info_db.update_sp(name_sp, param)
        results = BaseDA.call_sp(info_db,connection)
        return results

