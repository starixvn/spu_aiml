import datetime


class SPU_UpdateScanStatusDAModel(object):
    def __init__(self,*args):
        self.ip_ScannedDateTime: datetime = args[0]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_ScannedDateTime, self.op_ErrorMessage]