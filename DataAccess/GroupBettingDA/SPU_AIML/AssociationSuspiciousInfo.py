import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
import json
import pandas as pd
import time
from app import config
from Utilities import FunctionSupport


class InsertAssociationSuspiciousInfo:
    def execute(self, batches_data):
        try:
            from DataAccess.SPUAIMLDA import CommonDA
            common_da = CommonDA()
            common_da.insert_many('SPU_AIML_InsertAssociationSuspiciousInfo', batches_data, write_error_to_csv=True)
        except Exception as err:
            message_telegram = f'{config.ENV} | Error insert AssociationSuspiciousInfo in SPU when day-end: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError