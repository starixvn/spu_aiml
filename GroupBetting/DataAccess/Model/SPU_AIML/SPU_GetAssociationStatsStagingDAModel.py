class SPU_GetAssociationStatsStagingDAModel(object):
    def __init__(self,*args):
        self.ip_CustIDList: str = args[0]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_CustIDList, self.op_ErrorMessage]