import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from DataAccess.SPUAIMLDA import CommonDA


class InsertSystemParameter:
    def execute(self, date_insert):
        proc_name = 'SPU_AIML_UpdateScanStatus'
        data = [date_insert, None]
        common_da = CommonDA()
        common_da.insert_single(proc_name, data)
