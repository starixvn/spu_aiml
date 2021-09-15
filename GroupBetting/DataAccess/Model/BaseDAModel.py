import sys
# PROD
# sys.path.append("/home/vnteam/app/")
# LOCAL
sys.path.append("D:\\Project\\aiml_cleancode\\")
from Configuration.Configuration import config
from mysql.connector.pooling import MySQLConnectionPool
class BaseDAModel(object):
    def __init__(self, *args, **kwargs):
        self.database = args[0]
        self.host = args[1]
        self.port = args[2]
        self.user = args[3]
        self.pwd = args[4]
        self.sp = None
        self.param = None
        self.output_exception_msg = None
        self.output_sperror_msg = None
    
    def update_sp(self,sp,param):
        self.sp = sp
        self.param = param
        self.output_exception_msg = f"{config.app_name} | {config.ENV} | ERROR | Execute SP {self.sp} failed: "
        self.output_sperror_msg = f"{config.app_name} | {config.ENV} | ERROR | Error from SP {self.sp}: "
    

        