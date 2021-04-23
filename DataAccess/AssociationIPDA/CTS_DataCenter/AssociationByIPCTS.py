import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\\working\\aiml\\")
from Configuration.Configuration import config


class AssociationByIPCTSDA:

    def insert(self, batch_data, date_insert):
        from DataAccess.SPUAIMLDA import CommonDA
        proc_name = 'CTS_DC_Association_InsertAssociationByIP'
        message_telegram = f"{config.ENV} | Error insert Group Betting by IP to CTS DB: "
        common_da = CommonDA(db='cts')
        common_da.insert(proc_name, [batch_data], message_telegram, date_insert=date_insert)
