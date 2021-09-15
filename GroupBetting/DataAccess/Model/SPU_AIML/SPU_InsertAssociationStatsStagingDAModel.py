import json
class SPU_InsertAssociationStatsStagingDAModel(object):
    def __init__(self,*args):
        self.ip_StatsStaging: json = args[0]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_StatsStaging, self.op_ErrorMessage]
