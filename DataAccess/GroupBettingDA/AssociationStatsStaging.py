import sys
##PROD
#sys.path.append("/home/vnteam/app/")
##LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from Configuration.Configuration import config


class AssociationStatsStagingDA:

    def __init__(self):
        from DataAccess.CoreDA.SPUAIMLDA import CommonDA
        self.common_da = CommonDA()

    def truncate(self):
        self.common_da.truncate('AssociationStatsStaging')

    def get(self, custid_list):
        proc_name = 'SPU_AIML_GetAssociationStatsStaging'
        message_telegram = f'{config.ENV} | Error get data from AssociationStatsStaging in SPU when on-the-fly: '
        custid_proc_input = ''
        for id in custid_list[:-1]:
            custid_proc_input += str(id) + ', '
        custid_proc_input += str(custid_list[-1])
        proc_input = [custid_proc_input, None]
        dba_results = self.common_da.get(proc_name, proc_input, message_telegram)
        return dba_results

    def update(self, custid_list):
        message_telegram = f'{config.ENV} | Error Update Staging Status: '
        custid_proc_input = ''
        for id in custid_list[:-1]:
            custid_proc_input += str(id) + ', '
        custid_proc_input += str(custid_list[-1])
        dba_results = self.common_da.update('SPU_AIML_UpdateAssociationStatsStagingStatus', custid_proc_input, message_telegram)
        return dba_results

    def insert(self, batches_data):
        message_telegram = f'{config.ENV} | Error insert AssociationStats in SPU when day-end: '
        self.common_da.insert('SPU_AIML_InsertAssociationStatsStaging', batches_data, message_telegram, to_json=True)
