import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
from app import config
from Utilities import FunctionSupport


class InsertAssociationByIPCTS:

    def execute(self, batch_data, date_insert):
        try:
            from DataAccess.SPUAIMLDA import CommonDA
            proc_name = 'CTS_DC_Association_InsertAssociationByIP'
            data = [batch_data, date_insert, None]
            common_da = CommonDA()
            common_da.insert_single(proc_name, data)
        except Exception as e:
            message_telegram = f"{config.ENV} | Error insert Group Betting by IP to CTS DB: {e}"
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError
