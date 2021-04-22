import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
from app import config


class InsertAssociationSuspiciousInfo:

    def execute(self, batches_data):
        from DataAccess.SPUAIMLDA import CommonDA
        message_telegram = f'{config.ENV} | Error insert AssociationSuspiciousInfo in SPU when day-end: '
        common_da = CommonDA()
        common_da.insert('SPU_AIML_InsertAssociationSuspiciousInfo', batches_data, message_telegram, write_error_to_csv=True, to_json=True)
