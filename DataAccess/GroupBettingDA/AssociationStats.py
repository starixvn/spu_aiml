import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from Configuration.Configuration import config


class AssociationStatsDA:

    def __init__(self):
        from DataAccess.SPUAIMLDA import CommonDA
        self.common_da = CommonDA()

    def get(self, from_custid, to_custid):
        proc_name = 'SPU_AIML_GetAssociationStats'
        data = [from_custid, to_custid, None]
        message_telegram = f'GROUP BETTING | {config.ENV} | ERROR | Get data from SPU_AIML AssociationStats failed (at day-end): '
        dba_results = self.common_da.get(proc_name, data, message_telegram)
        return dba_results

    def insert(self, batches_data, date_insert):
        message_telegram = f'GROUP BETTING | {config.ENV} | ERROR | Insert AssociationStats to SPU_AIML DB failed (at day-end): '
        self.common_da.insert('SPU_AIML_InsertAssociationStats', batches_data, message_telegram, date_insert=date_insert, to_json=True)
