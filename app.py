from Configuration.Configuration import config
from DataAccess.DataAccessConnection import connection_pool_cts_datacenter,connection_pool_spu_aiml
import logging
import warnings
from TaskManagement.GroupBettingManagement.GroupBettingController import GroupBettingController
import os
import torch
warnings.filterwarnings("ignore")
logging.basicConfig(filename=os.path.join(config.save_dir_log, config.log_name), level=logging.INFO)


if __name__ == "__main__":
    GroupBettingController.run()
    
    
    
