from Configuration.Configuration import Configuration
ENV='LOCAL'
if ENV=='LOCAL':
    config = Configuration("localconfig.ini",ENV)
else:
    config = Configuration("proconfig.ini",ENV)
import logging
import warnings
from DataAccess.GroupBettingDA.SPU_AIML import AssociationStatsStaging
from TaskManagement.GroupBettingManagement import main
import os
import torch

warnings.filterwarnings("ignore")
logging.basicConfig(filename=os.path.join(config.save_dir_log, config.log_name), level=logging.INFO)


if __name__ == "__main__":
    #region Clear and Clean Data
    AssociationStatsStaging.TruncateAssociationStatsStaging()
    check_cus_files=os.listdir(config.root)
    if config.cus_list_fn in check_cus_files:
        os.remove(os.path.join(config.root,config.cus_list_fn))
    if config.cus_dict_fn in check_cus_files:
        os.remove(os.path.join(config.root,config.cus_dict_fn))
    
    main.run(config)
    
    
