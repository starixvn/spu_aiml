import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from Configuration.Configuration import config


class AssociationByAICTSDA:

    def insert(self, batches_data, date_insert):
        from DataAccess.SPUAIMLDA import CommonDA
        proc_name = 'CTS_DC_Association_InsertAssociationByAI'
        error_message = f'GROUP BETTING | {config.ENV} | ERROR | Insert AssociationByAI to CTS DB failed: '
        common_da = CommonDA(db='cts')
        common_da.insert(proc_name, batches_data, error_message, date_insert=date_insert, to_json=True)
