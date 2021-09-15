from Configuration.Configuration import config
import logging
import warnings
from TaskManagement.GroupBettingManagement.GroupBettingController import GroupBettingController
import os
import torch
warnings.filterwarnings("ignore")
logging.basicConfig(filename=os.path.join(config.save_dir_log, config.log_name), level=logging.INFO)


if __name__ == "__main__":
    GroupBettingController.run()
    
    
    
