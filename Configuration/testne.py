import os
import configparser
class Foo(object):
    def __init__(self, *args):
        
        self.path= os.path.dirname(__file__)
        config = configparser.ConfigParser()
        config.read(os.path.join(self.path,args[0]))
        
        self.config= config
        self.dir = self.GetSaveDirectoryLog(self.config)
        
        
    @classmethod
    def GetSaveDirectoryLog(self,config):
        config.sections()
        return config['DEFAULT']['SAVE_DIR_LOG']