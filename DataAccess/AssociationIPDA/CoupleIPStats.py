import sys

# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL

sys.path.append("/\\")
from Configuration.Configuration import config
from DataAccess.CoreDA.SPUAIMLDA import CommonDA


class CoupleIPStatsDA:

    def insert(self, batches_data, date_insert):
        message_telegram = f"GROUP BETTING | {config.ENV} | ERROR | Insert CoupleIPStats to SPU_AIML DB failed: "
        common_da = CommonDA()
        common_da.insert('SPU_AIML_InsertCoupleIPStats', batches_data, message_telegram, save_ip=True, save_ip_date=date_insert, to_json=True)
