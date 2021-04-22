import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
from app import config


class InsertAssociationByAISPU:

    def execute(self, batches_data):
        from DataAccess.SPUAIMLDA import CommonDA
        proc_name = 'SPU_AIML_InsertAssociationByAI'
        message_telegram = f'{config.ENV} | Error insert AssociationByAI in SPU when day-end: '
        common_da = CommonDA()
        common_da.insert(proc_name, batches_data, message_telegram, to_json=True)
