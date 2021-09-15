import json


class SPU_InsertCoupleIPStatsDAModel(object):
    def __init__(self,*args):
        self.ip_CoupleIPStats: json = args[0]
        self.op_ErrorMessage = None
        
    def __call__(self):
        return [self.ip_CoupleIPStats, self.op_ErrorMessage]