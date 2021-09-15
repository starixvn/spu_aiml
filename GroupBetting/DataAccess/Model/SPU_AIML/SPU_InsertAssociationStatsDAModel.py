import json
import datetime
class SPU_InsertAssociationStatsDAModel(object):
    def __init__(self,*args):
        self.ip_DailyStats: json = args[0]
        self.ip_ScanDate: datetime = args[1]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_DailyStats, self.ip_ScanDate, self.op_ErrorMessage]
