import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
import json
import pandas as pd
import time
from app import config
from Utilities import FunctionSupport
from DataAccess.SPUAIMLDA import CommonDA


class InsertAssociationSuspiciousInfo:
    def execute(self, batches_data):
        try:
            common_da = CommonDA()
            common_da.insert_many('SPU_AIML_InsertAssociationSuspiciousInfo', batches_data, write_error_to_csv=True)
        except Exception as err:
            message_telegram = f'{config.ENV} | Error insert AssociationSuspiciousInfo in SPU when day-end: {err}'
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError