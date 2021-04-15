# ENV = 'LOCAL'
# print(ENV.capitalize())
import configparser
import os
class SystemConfig():
    def __init__(self, ENV):
        self.ENV = ENV
        path = os.path.dirname(__file__)
        print('path',path)
        config = configparser.ConfigParser()
        # if ENV=='PRO':
        config.read(os.path.join(path,ENV.capitalize()+'config.ini'))
        # else:
            # config.read(os.path.join(path,'proconfig.ini'))
        self.config= config
    
    @classmethod
    def GetSaveDirectoryLog(self,config):
        config.config.sections()
        return config.config['DEFAULT']['SAVE_DIR_LOG']

a = SystemConfig('LOCAL')
# b = a.GetSaveDirectoryLog(a)
# print(a.ENV)
# print('GetSaveDirectoryLog',b)