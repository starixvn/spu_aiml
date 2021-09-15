import datetime
import json


class CTS_InsertAssociationByIPDAModel(object):
    def __init__(self,*args):
        self.ip_CoupleIPStats: json = args[0]
        self.ip_ScanDate: datetime = args[1]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_CoupleIPStats, self.ip_ScanDate, self.op_ErrorMessage]