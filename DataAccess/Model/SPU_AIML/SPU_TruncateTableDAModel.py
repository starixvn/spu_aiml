class SPU_TruncateTableDAModel(object):
    def __init__(self,*args):
        self.ip_TableName: str = args[0]
        
    def __call__(self):
        return [self.ip_TableName]