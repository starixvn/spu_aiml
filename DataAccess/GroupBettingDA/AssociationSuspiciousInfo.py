import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
from app import config


class AssociationSuspiciousInfoDA:

    def insert(self, batches_data):
        from DataAccess.SPUAIMLDA import CommonDA
        message_telegram = f'GROUP BETTING | {config.ENV} | ERROR | Insert AssociationSuspiciousInfo to SPU_AIML (at day-end): '
        common_da = CommonDA()
        common_da.insert('SPU_AIML_InsertAssociationSuspiciousInfo', batches_data, message_telegram, write_error_to_csv=True, to_json=True)
