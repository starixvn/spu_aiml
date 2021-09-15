import json
class SPU_InsertAssociationByAIDAModel(object):
    def __init__(self,*args):
        self.ip_Association: json = args[0]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_Association, self.op_ErrorMessage]