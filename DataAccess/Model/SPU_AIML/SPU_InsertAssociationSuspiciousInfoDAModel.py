import json


class SPU_InsertAssociationSuspiciousInfoDAModel(object):
    def __init__(self,*args):
        self.ip_SuspiciousInfo: json = args[0]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_SuspiciousInfo, self.op_ErrorMessage]