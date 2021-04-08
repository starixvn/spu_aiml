import configparser
import os

class Configuration(object):
    """description of class"""
    def __init__(self, *args, **kwargs):
        path= os.path.dirname(__file__)
        config = configparser.ConfigParser()
        config.read(os.path.join(path,args[0]))
        self.config= config
        self.ENV = args[1]
        
        # define log config
        self.save_dir_log = self.GetSaveDirectoryLog(self.config)
        self.log_name = self.GetLogName(self.config)
        # define GroupBetting config
        self.config_retry = int(self.getRetry(self.config))
        self.time_sleep = int(self.getTimeSleep(self.config))
        self.percent_score = int(self.getPercentScore(self.config))
        self.time_threshold = int(self.GetTimeThreshold(self.config))
        self.combination_threshold = int(self.GetCombinationThreshold(self.config))
        # define paths
        self.root=self.GetSaveDataDir(self.config)
        self.root_orig=self.GetPathCsvFile(self.config)
        self.orig_fn=self.GetNameFile(self.config)
        self.match_breaking=self.GetMatchBreaking(self.config)
        self.cus_list_fn=self.GetListName(self.config)
        self.cus_dict_fn=self.GetDictName(self.config)
        self.mlm_dict_fn=self.GetMatchLeagueMap(self.config)
        self.backup=self.GetBackUp(self.config)
        self.errorFolder = self.GetErrorFolder(self.config)

        # define chunk_size for DB saving
        self.chunk_size = int(self.getChunkSize(self.config))

        # define nb_workers_phase_1
        self.nb_workers_phase_1 = int(self.getNumberWorkerPhase1(self.config))

        # define nb_workers_phase_2
        self.nb_workers_phase_2 = int(self.getNumberWorkerPhase2(self.config))

        # define batch size for get customers in phase 2
        self.num_batch_cus = int(self.getNumBatchCus(self.config))

        self.aimluser=self.getSPU_AIMLUsername(self.config)
        self.aimlpwd=self.getSPU_AIMLPassword(self.config)
        self.aimlhost=self.getSPU_AIMLHost(self.config)
        self.aimlport=self.getSPU_AIMLPort(self.config)
        self.aimldb=self.getSPU_AIMLDatabaseName(self.config)

        self.ctsuser=self.getCTS_DataCenterUsername(self.config)
        self.ctspwd=self.getCTS_DataCenterPassword(self.config)
        self.ctshost=self.getCTS_DataCenterHost(self.config)
        self.ctsport=self.getCTS_DataCenterPort(self.config)
        self.ctsdb=self.getCTS_DataCenterDatabaseName(self.config)

        # define is transfer data to CTS
        self.transfer_score = self.getTransferDataScore(self.config)
        self.transfer_ip = self.getTransferDataIP(self.config)
        
       
    @classmethod
    def GetSaveDirectoryLog(self,config):
        config.sections()
        return config['DEFAULT']['SAVE_DIR_Log']

    @classmethod
    def GetNameFile(self,config):
        config.sections()
        return config['DEFAULT']['NAME_MATCH']
    
    @classmethod
    def GetListName(self,config):
        config.sections()
        return config['DEFAULT']['LIST_NAME']
    
    @classmethod
    def GetDictName(self,config):
        config.sections()
        return config['DEFAULT']['DICT_NAME']

    @classmethod
    def GetPathCsvFile(self,config):
        config.sections()
        return config['DEFAULT']['GET_PATH_CSVFILE']

    @classmethod
    def GetLogName(self,config):
        config.sections()
        return config['DEFAULT']['LOG_NAME'] 

    @classmethod
    def GetMajorLeagueName(self, config):
        config.sections()
        return config['DEFAULT']['NAME_LEAGUE']

    @classmethod   
    def GetMatchLeagueMapping(self, config):
        config.sections()
        return config['DEFAULT']['NAME_LEAGUESPORT']

    @classmethod   
    def GetSaveDataDir(self, config):
        config.sections()
        return config['DEFAULT']['SAVE_DATA_DIR']
    
    @classmethod   
    def GetErrorFolder(self, config):
        config.sections()
        return config['DEFAULT']['ERROR_FOLDER']
    
    @classmethod   
    def GetBackUp(self, config):
        config.sections()
        return config['DEFAULT']['BACK_UP']

    @classmethod
    def GetMatchLeagueMap(self, config):
        config.sections()
        return config['DEFAULT']['MATCH_LEAGUE_MAP']

    @classmethod
    def GetMatchBreaking(self, config):
        config.sections()
        return config['DEFAULT']['MATCH_BREAKING']
    
    @classmethod
    def GetTimeThreshold(self,config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['TIME_THRESHOLD']
    
    @classmethod
    def GetCombinationThreshold(self,config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['COMBINATION_THRESHOLD']

    @classmethod
    def getServerName(self, config):
        config.sections()
        return config['DATABASE']['SERVER']

    @classmethod
    def getSPU_AIMLDatabaseName(self, config):
        config.sections()
        return config['DATABASE SPU_AIML']['DATABASE_NAME']

    @classmethod
    def getSPU_AIMLUsername(self, config):
        config.sections()
        return config['DATABASE SPU_AIML']['USERNAME']

    @classmethod
    def getSPU_AIMLPassword(self, config):
        config.sections()
        return config['DATABASE SPU_AIML']['PASSWORD']
    
    @classmethod
    def getSPU_AIMLHost(self, config):
        config.sections()
        return config['DATABASE SPU_AIML']['HOST']

    @classmethod
    def getSPU_AIMLPort(self, config):
        config.sections()
        return config['DATABASE SPU_AIML']['PORT']
    
    @classmethod
    def getCTS_DataCenterDatabaseName(self, config):
        config.sections()
        return config['DATABASE CTS_DataCenter']['DATABASE_NAME']

    @classmethod
    def getCTS_DataCenterUsername(self, config):
        config.sections()
        return config['DATABASE CTS_DataCenter']['USERNAME']

    @classmethod
    def getCTS_DataCenterPassword(self, config):
        config.sections()
        return config['DATABASE CTS_DataCenter']['PASSWORD']
    
    @classmethod
    def getCTS_DataCenterHost(self, config):
        config.sections()
        return config['DATABASE CTS_DataCenter']['HOST']

    @classmethod
    def getCTS_DataCenterPort(self, config):
        config.sections()
        return config['DATABASE CTS_DataCenter']['PORT']

    @classmethod
    def getPercentScore(self, config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['PERCENT_SCORE']
    
    @classmethod
    def getTimeSleep(self, config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['TIME_SLEEP']
    
    @classmethod
    def getRetry(self, config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['RETRY']
    
    @classmethod
    def getNumberWorkerPhase1(self, config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['NB_WORKER_PHASE_1']
    
    @classmethod
    def getNumberWorkerPhase2(self, config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['NB_WORKER_PHASE_2']
    
    @classmethod
    def getChunkSize(self, config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['CHUNK_SIZE']
    
    @classmethod
    def getNumBatchCus(self, config):
        config.sections()
        return config['GROUPBETTINGCONFIG']['NUM_BATCH_CUS']
    
    @classmethod
    def getTransferDataScore(self, config):
        config.sections()
        return config['ACTION_CTS'].getboolean('TRANSFER_DATASCORE')
    
    @classmethod
    def getTransferDataIP(self, config):
        config.sections()
        return config['ACTION_CTS'].getboolean('TRANSFER_DATAIP')
    
    





