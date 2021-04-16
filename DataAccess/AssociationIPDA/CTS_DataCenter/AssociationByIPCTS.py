import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from app import config
from Utilities import FunctionSupport
from DataAccess.SPUAIMLDA import CommonDA


class InsertAssociationByIPCTS:

    def execute(self, batch_data, date_insert):
        try:
            proc_name = 'CTS_DC_Association_InsertAssociationByIP'
            data = [batch_data, date_insert, None]
            common_da = CommonDA()
            common_da.insert_single(proc_name, data)
        except Exception as e:
            message_telegram = f"{config.ENV} | Error insert Group Betting by IP to CTS DB: {e}"
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError
