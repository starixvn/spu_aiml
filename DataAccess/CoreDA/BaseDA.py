import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
#sys.path.append("D:\\Project\\aiml_cleancode\\")
from Configuration.Configuration import config
from DataAccess.CoreDA.CommonDA import CommonDA
from Utilities import Utilities


class BaseDA(object):
    def call_sp(info_db):
        conn = info_db.pool.get_connection()
        cursor = conn.cursor()
        try:
            sp_output = cursor.callproc(info_db.sp,info_db.param())
            if sp_output[-1] != None:
                Utilities.notify_logging(info_db.sp_mess + str(sp_output))
            dba_results = [r.fetchall() for r in cursor.stored_results()]
            conn.commit()
            conn.close()
            cursor.close()
            return dba_results
        except Exception as err:
            Utilities.notify_logging(info_db.exception_mess +str(err))
            
    def execute(name_sp, info_db, param):
        info_db.update_sp(name_sp,param)
        results = BaseDA.call_sp(info_db)
        return results
        