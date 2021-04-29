import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from Configuration.Configuration import config
class BaseDAModel(object):
    def __init__(self, *args, **kwargs):
        self.database = args[0]
        self.host = args[1]
        self.port = args[2]
        self.user = args[3]
        self.pwd = args[4]
        self.sp = None
        self.param = None
        self.exception_mess = None
        self.sp_mess = None
        self.sp_output = None
    
    def __call__(self,sp,param):
        self.sp = sp
        self.param = param
        self.exception_mess = f"{config.app_name} | {config.ENV} | ERROR | Execute SP {self.sp} failed: "
        self.sp_mess = f"{config.app_name} | {config.ENV} | ERROR | Error from SP {self.sp}: {self.sp_output} | With CusList {self.param}"