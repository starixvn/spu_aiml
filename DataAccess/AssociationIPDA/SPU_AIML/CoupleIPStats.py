import sys

# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL

sys.path.append("D:\\\working\\aiml\\")
from app import config
from DataAccess.SPUAIMLDA import CommonDA


class InsertCoupleIPStats:

    def execute(self, batches_data, date_insert):
        message_telegram = f"{config.ENV} | Error insert CoupleIPStats to SPU DB: "
        common_da = CommonDA()
        common_da.insert('SPU_AIML_InsertCoupleIPStats', batches_data, message_telegram, save_ip=True, save_ip_date=date_insert, to_json=True)
