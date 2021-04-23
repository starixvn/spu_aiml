import configparser
import os


class Configuration(object):
    """description of class"""
    def __init__(self, *args, **kwargs):
        path = os.path.dirname(__file__)
        config = configparser.ConfigParser()
        config.read(os.path.join(path, args[0]))
        self.config = config
        self.ENV = args[1]

        # define paths
        self.save_dir_log = self.getDataStrConfig(
            self.config, 'DEFAULT', 'SAVE_DIR_LOG')
        self.log_name = self.getDataStrConfig(
            self.config, 'DEFAULT', 'LOG_NAME')
        self.root = self.getDataStrConfig(
            self.config, 'DEFAULT', 'SAVE_DATA_DIR')
        self.root_orig = self.getDataStrConfig(
            self.config, 'DEFAULT', 'GET_PATH_CSVFILE')
        self.orig_fn = self.getDataStrConfig(
            self.config, 'DEFAULT', 'NAME_MATCH')
        self.match_breaking = self.getDataStrConfig(
            self.config, 'DEFAULT', 'MATCH_BREAKING')
        self.cus_list_fn = self.getDataStrConfig(
            self.config, 'DEFAULT', 'LIST_NAME')
        self.cus_dict_fn = self.getDataStrConfig(
            self.config, 'DEFAULT', 'DICT_NAME')
        self.mlm_dict_fn = self.getDataStrConfig(
            self.config, 'DEFAULT', 'MATCH_LEAGUE_MAP')
        self.backup = self.getDataStrConfig(self.config, 'DEFAULT', 'BACK_UP')
        self.errorFolder = self.getDataStrConfig(
            self.config, 'DEFAULT', 'ERROR_FOLDER')

        # define GroupBetting config
        self.config_retry = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'RETRY'))
        self.time_sleep = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'TIME_SLEEP'))
        self.percent_score = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'PERCENT_SCORE'))
        self.time_threshold = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'TIME_THRESHOLD'))
        self.combination_threshold = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'COMBINATION_THRESHOLD'))
        self.chunk_size = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'CHUNK_SIZE'))
        self.nb_workers_phase_1 = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'NB_WORKER_PHASE_1'))
        self.nb_workers_phase_2 = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'NB_WORKER_PHASE_2'))
        self.num_batch_cus = int(self.getDataStrConfig(
            self.config, 'GROUPBETTINGCONFIG', 'NUM_BATCH_CUS'))
        
        # define information db SPU
        self.aimluser = self.getDataStrConfig(
            self.config, 'SPU_AIML_DB', 'USERNAME')
        self.aimlpwd = self.getDataStrConfig(
            self.config, 'SPU_AIML_DB', 'PASSWORD')
        self.aimlhost = self.getDataStrConfig(
            self.config, 'SPU_AIML_DB', 'HOST')
        self.aimlport = self.getDataStrConfig(
            self.config, 'SPU_AIML_DB', 'PORT')
        self.aimldb = self.getDataStrConfig(
            self.config, 'SPU_AIML_DB', 'DATABASE_NAME')

        # define information db CTS
        self.ctsuser = self.getDataStrConfig(
            self.config, 'CTS_DataCenter_DB', 'USERNAME')
        self.ctspwd = self.getDataStrConfig(
            self.config, 'CTS_DataCenter_DB', 'PASSWORD')
        self.ctshost = self.getDataStrConfig(
            self.config, 'CTS_DataCenter_DB', 'HOST')
        self.ctsport = self.getDataStrConfig(
            self.config, 'CTS_DataCenter_DB', 'PORT')
        self.ctsdb = self.getDataStrConfig(
            self.config, 'CTS_DataCenter_DB', 'DATABASE_NAME')

        # define is transfer data to CTS
        self.transfer_score = self.getDataBooleanConfig(
            self.config, 'ACTION_CTS', 'TRANSFER_DATASCORE')
        self.transfer_ip = self.getDataBooleanConfig(
            self.config, 'ACTION_CTS', 'TRANSFER_DATASCORE')


    @classmethod
    def getDataStrConfig(self, config, parent, child):
        config.sections()
        return config[parent][child]

    @classmethod
    def getDataBooleanConfig(self, config, parent, child):
        config.sections()
        return config[parent].getboolean(child)


ENV='LOCAL'
if ENV=='LOCAL':
    config = Configuration("localconfig.ini",ENV)
else:
    config = Configuration("proconfig.ini",ENV)
