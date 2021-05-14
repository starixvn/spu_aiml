from DataAccess.CoreDA.CommonDA import CommonDA
from Configuration.Configuration import config
from DataAccess.Model.BaseDAModel import BaseDAModel

class DataAccessConnection(object):
    def __init__(self,pool):
        self.conn = pool.get_connection()
        self.cursor = self.conn.cursor()
        
    def __del__(self):
        self.conn.close()
        self.cursor.close()
    
    global spu_aiml,cts_datacenter
    spu_aiml = BaseDAModel(config.aimldb, config.aimlhost, config.aimlport, config.aimluser, config.aimlpwd)
    cts_datacenter = BaseDAModel(config.ctsdb, config.ctshost, config.ctsport, config.ctsuser, config.ctspwd)
    
    global connection_pool_spu_aiml,connection_pool_cts_datacenter
    connection_pool_spu_aiml = CommonDA.create_pool(spu_aiml)
    connection_pool_cts_datacenter = CommonDA.create_pool(cts_datacenter)