import configparser
import os

class ProConfiguration(object):
    """description of class"""
    def __init__(self, *args, **kwargs):
        path= os.path.dirname(__file__)
        config = configparser.ConfigParser()
        config.read(os.path.join(path,'proconfig.ini'))
        self.config= config
        
       
    @classmethod
    def GetSaveDirectoryLog(self,config):
        config.config.sections()
        return config.config['DEFAULT']['SAVE_DIR_Log']

    @classmethod
    def GetNameFile(self,config):
        config.config.sections()
        return config.config['DEFAULT']['NAME_MATCH']
    
    @classmethod
    def GetListName(self,config):
        config.config.sections()
        return config.config['DEFAULT']['LIST_NAME']
    
    @classmethod
    def GetDictName(self,config):
        config.config.sections()
        return config.config['DEFAULT']['DICT_NAME']

    @classmethod
    def GetPathCsvFile(self,config):
        config.config.sections()
        return config.config['DEFAULT']['GET_PATH_CSVFILE']

    @classmethod
    def GetLogName(self,config):
        config.config.sections()
        return config.config['DEFAULT']['LOG_NAME'] 

    @classmethod
    def GetMajorLeagueName(self, config):
        config.config.sections()
        return config.config['DEFAULT']['NAME_LEAGUE']

    @classmethod   
    def GetMatchLeagueMapping(self, config):
        config.config.sections()
        return config.config['DEFAULT']['NAME_LEAGUESPORT']

    @classmethod   
    def GetSaveDataDir(self, config):
        config.config.sections()
        return config.config['DEFAULT']['SAVE_DATA_DIR']
    
    @classmethod   
    def GetBackUp(self, config):
        config.config.sections()
        return config.config['DEFAULT']['BACK_UP']

    @classmethod
    def GetMatchLeagueMap(self, config):
        config.config.sections()
        return config.config['DEFAULT']['MATCH_LEAGUE_MAP']

    @classmethod
    def GetMatchBreaking(self, config):
        config.config.sections()
        return config.config['DEFAULT']['MATCH_BREAKING']
    
    @classmethod
    def GetTimeThreshold(self,config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['TIME_THRESHOLD']
    
    @classmethod
    def GetCombinationThreshold(self,config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['COMBINATION_THRESHOLD']

    @classmethod
    def getServerName(self, config):
        config.config.sections()
        return config.config['DATABASE']['SERVER']

    @classmethod
    def getSPU_AIMLDatabaseName(self, config):
        config.config.sections()
        return config.config['DATABASE SPU_AIML']['DATABASE_NAME']

    @classmethod
    def getSPU_AIMLUsername(self, config):
        config.config.sections()
        return config.config['DATABASE SPU_AIML']['USERNAME']

    @classmethod
    def getSPU_AIMLPassword(self, config):
        config.config.sections()
        return config.config['DATABASE SPU_AIML']['PASSWORD']
    
    @classmethod
    def getSPU_AIMLHost(self, config):
        config.config.sections()
        return config.config['DATABASE SPU_AIML']['HOST']

    @classmethod
    def getSPU_AIMLPort(self, config):
        config.config.sections()
        return config.config['DATABASE SPU_AIML']['PORT']
    
    @classmethod
    def getCTS_DataCenterDatabaseName(self, config):
        config.config.sections()
        return config.config['DATABASE CTS_DataCenter']['DATABASE_NAME']

    @classmethod
    def getCTS_DataCenterUsername(self, config):
        config.config.sections()
        return config.config['DATABASE CTS_DataCenter']['USERNAME']

    @classmethod
    def getCTS_DataCenterPassword(self, config):
        config.config.sections()
        return config.config['DATABASE CTS_DataCenter']['PASSWORD']
    
    @classmethod
    def getCTS_DataCenterHost(self, config):
        config.config.sections()
        return config.config['DATABASE CTS_DataCenter']['HOST']

    @classmethod
    def getCTS_DataCenterPort(self, config):
        config.config.sections()
        return config.config['DATABASE CTS_DataCenter']['PORT']

    @classmethod
    def getPercentScore(self, config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['PERCENT_SCORE']
    
    @classmethod
    def getTimeSleep(self, config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['TIME_SLEEP']
    
    @classmethod
    def getRetry(self, config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['RETRY']
    
    @classmethod
    def getNumberWorkerPhase1(self, config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['NB_WORKER_PHASE_1']
    
    @classmethod
    def getNumberWorkerPhase2(self, config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['NB_WORKER_PHASE_2']
    
    @classmethod
    def getChunkSize(self, config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['CHUNK_SIZE']

    @classmethod
    def getNumBatchCus(self, config):
        config.config.sections()
        return config.config['GROUPBETTINGCONFIG']['NUM_BATCH_CUS']
    
    @classmethod
    def getTransferDataScore(self, config):
        config.config.sections()
        return config.config['ACTION_CTS'].getboolean('TRANSFER_DATASCORE')
    
    @classmethod
    def getTransferDataIP(self, config):
        config.config.sections()
        return config.config['ACTION_CTS'].getboolean('TRANSFER_DATAIP')




