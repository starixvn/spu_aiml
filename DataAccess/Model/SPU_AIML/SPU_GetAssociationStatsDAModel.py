class SPU_GetAssociationStatsDAModel(object):
    def __init__(self,*args):
        self.ip_FromCustID1: int = args[0]
        self.ip_ToCustID1: int = args[1]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_FromCustID1, self.ip_ToCustID1, self.op_ErrorMessage]