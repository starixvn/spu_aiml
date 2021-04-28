import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("/\\")
from Configuration.Configuration import config
from DataAccess.CoreDA.SPUAIMLDA import CommonDA


class AssociationByAISPUDA:

    def insert(self, batches_data):
        proc_name = 'SPU_AIML_InsertAssociationByAI'
        message_telegram = f'GROUP BETTING | {config.ENV} | ERROR | Insert AssociationByAI to SPU_AIML DB failed: '
        common_da = CommonDA()
        common_da.insert(proc_name, batches_data, message_telegram, to_json=True)
