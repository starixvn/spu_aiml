import sys

# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
from DataAccess.AssociationIPDA.CTS_DataCenter.AssociationByIPCTS import InsertAssociationByIPCTS

sys.path.append("D:\\Project\\aiml_cleancode\\")
import json
import pandas as pd
from app import config
from Utilities import FunctionSupport
from DataAccess.SPUAIMLDA import CommonDA


class InsertCoupleIPStats:
    def execute(self, batches_data, date_insert):
        try:
            common_da = CommonDA()
            for data in batches_data:
                json_objIP1 = json.dumps(data)
                dba_results = common_da.insert_single('SPU_AIML_InsertCoupleIPStats', [json_objIP1,None])
                if config.transfer_ip:
                    save_dba_results(dba_results, date_insert)

        except Exception as err:
            message_telegram = f"{config.ENV} | Error insert CoupleIPStats to SPU DB: {err}"
            FunctionSupport.notify_logging(message_telegram)
            raise ValueError


def save_dba_results(dba_results, date_insert):
    if len(dba_results[0]) > 0:
        df_CTS = pd.DataFrame(dba_results[0], columns=[
            "C1",
            "C2"])
        full_data_IPCTS_dba = df_CTS.to_json(orient="records")
        insert_association_by_IPCTS = InsertAssociationByIPCTS()
        insert_association_by_IPCTS.execute(full_data_IPCTS_dba, date_insert)
