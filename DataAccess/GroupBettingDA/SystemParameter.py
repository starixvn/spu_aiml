import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from DataAccess.CoreDA.SPUAIMLDA import CommonDA
from app import config


class SystemParameterDA:
    def insert(self, date_insert):
        proc_name = 'SPU_AIML_UpdateScanStatus'
        message_telegram = f"GROUP BETTING | {config.ENV} | ERROR | Update SPU_AIML SystemParameter failed: "
        common_da = CommonDA()
        common_da.insert(proc_name, [date_insert], message_telegram)
