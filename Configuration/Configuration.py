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
    def GetSaveDirectoryModel(self,config):
        config.config.sections()
        return config.config['DEFAULT']['SAVE_DIR_MODEL']

    @classmethod
    def GetNameFile(self,config):
        config.config.sections()
        return config.config['DEFAULT']['NAME_MATCH']

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
    
    def GetTemp1(self, config):
        config.config.sections()
        return config.config['DEFAULT']['TEMP1']
    
    def GetTemp2(self, config):
        config.config.sections()
        return config.config['DEFAULT']['TEMP2']
    
    def GetMatchOuput(self, config):
        config.config.sections()
        return config.config['DEFAULT']['MATCH_OUTPUT']
    
    def GetScoreOuput(self, config):
        config.config.sections()
        return config.config['DEFAULT']['SCORE_OUTPUT']

    def GetTransOuput(self, config):
        config.config.sections()
        return config.config['DEFAULT']['TRANS_OUTPUT']

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





