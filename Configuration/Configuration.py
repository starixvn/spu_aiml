import configparser
import os

class Configuration(object):
    """description of class"""
    def __init__(self, *args, **kwargs):
        path= os.path.dirname(__file__)
        config = configparser.ConfigParser()
        config.read(os.path.join(path,'config.ini'))
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

    def GetMajorLeagueName(self, config):
        config.config.sections()
        return config.config['DEFAULT']['NAME_LEAGUE']
    
    def GetMatchLeagueMapping(self, config):
        config.config.sections()
        return config.config['DEFAULT']['NAME_LEAGUESPORT']
    
    def GetSaveDataDir(self, config):
        config.config.sections()
        return config.config['DEFAULT']['SAVE_DATA_DIR']
    
    def GetMatchLeagueMap(self, config):
        config.config.sections()
        return config.config['DEFAULT']['MATCH_LEAGUE_MAP']
    
    def GetTemp2(self, config):
        config.config.sections()
        return config.config['DEFAULT']['TEMP2']
    
    def GetMatchBreaking(self, config):
        config.config.sections()
        return config.config['DEFAULT']['MATCH_BREAKING']
    
    def GetScoreOuput(self, config):
        config.config.sections()
        return config.config['DEFAULT']['SCORE_OUTPUT']

    def GetTransOuput(self, config):
        config.config.sections()
        return config.config['DEFAULT']['TRANS_OUTPUT']
    
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
    def getDatabaseName(self, config):
        config.config.sections()
        return config.config['DATABASE']['DATABASE_NAME']

    @classmethod
    def getUsername(self, config):
        config.config.sections()
        return config.config['DATABASE']['USERNAME']

    @classmethod
    def getPassword(self, config):
        config.config.sections()
        return config.config['DATABASE']['PASSWORD']

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





