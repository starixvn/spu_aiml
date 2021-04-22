import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
from app import config


class AssociationStats:

    def __init__(self):
        from DataAccess.SPUAIMLDA import CommonDA
        self.common_da = CommonDA()

    def get(self, from_custid, to_custid):
        proc_name = 'SPU_AIML_GetAssociationStats'
        data = [from_custid, to_custid, None]
        message_telegram = f'{config.ENV} | Error get data from AssociationStats when day-end: '
        dba_results = self.common_da.get(proc_name, data, message_telegram)
        return dba_results

    def insert(self, batches_data, date_insert):
        message_telegram = f'{config.ENV} | Error insert AssociationStats in SPU when day-end: '
        self.common_da.insert('SPU_AIML_InsertAssociationStats', batches_data, message_telegram, date_insert=date_insert, to_json=True)
