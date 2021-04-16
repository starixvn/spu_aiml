import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from app import config
from Utilities import FunctionSupport
from DataAccess.SPUAIMLDA import CommonDA


class AssociationStatsStaging:
    def __init__(self):
        self.common_da = CommonDA()

    def truncate(self):
        proc_name = 'SPU_AIML_DBA_Truncate_Table'
        data = ['AssociationStatsStaging']
        self.common_da.insert_single(proc_name, data)

    def get(self, custid_list):
        proc_name = 'SPU_AIML_GetAssociationStatsStaging'
        data = ['AssociationStatsStaging']
        dba_results = self.common_da.get(proc_name, data)
        return dba_results

    def update(self, custid_list):
        data = ['AssociationStatsStaging']
        dba_results = self.common_da.update('SPU_AIML_UpdateAssociationStatsStagingStatus', data)
        return dba_results

    def insert(self, batches_data):
        try:
            self.common_da.insert_many('SPU_AIML_InsertAssociationStats', batches_data)
        except Exception as err:
            message_telegram = f'{config.ENV} | Error insert AssociationStats in SPU when day-end: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError
