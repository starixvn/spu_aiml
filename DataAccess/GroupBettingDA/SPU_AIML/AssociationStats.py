import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
from app import config
from Utilities import FunctionSupport


class AssociationStats:
    def __init__(self):
        from DataAccess.SPUAIMLDA import CommonDA
        self.common_da = CommonDA()

    def get(self, from_custid, to_custid):
        try:
            proc_name = 'SPU_AIML_GetAssociationStats'
            data = [from_custid, to_custid, None]
            dba_results = self.common_da.get(proc_name, data)
            return dba_results
        except Exception as err:
            message_telegram = f'{config.ENV} | Error get data from AssociationStats when day-end: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError

    def insert(self, batches_data):
        try:
            self.common_da.insert_many('SPU_AIML_InsertAssociationStats', batches_data)
        except Exception as err:
            message_telegram = f'{config.ENV} | Error insert AssociationStats in SPU when day-end: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError
