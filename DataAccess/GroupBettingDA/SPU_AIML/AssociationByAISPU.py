import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
from app import config
from Utilities import FunctionSupport


class InsertAssociationByAISPU:
    def execute(self, batches_data):
        from DataAccess.SPUAIMLDA import CommonDA
        try:
            proc_name = 'SPU_AIML_InsertAssociationByAI'
            common_da = CommonDA()
            common_da.insert_many(proc_name, batches_data, date_insert)
        except Exception as err:
            message_telegram = f'{config.ENV} | Error insert AssociationByAI in SPU when day-end: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError