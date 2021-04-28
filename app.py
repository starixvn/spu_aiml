import logging
import os
import warnings

from Configuration.Configuration import config
from Controller import GroupBettingController

warnings.filterwarnings("ignore")
logging.basicConfig(filename=os.path.join(config.save_dir_log, config.log_name), level=logging.INFO)


if __name__ == "__main__":
    check_cus_files=os.listdir(config.root)
    if config.cus_list_fn in check_cus_files:
        os.remove(os.path.join(config.root,config.cus_list_fn))
    if config.cus_dict_fn in check_cus_files:
        os.remove(os.path.join(config.root,config.cus_dict_fn))
    
    GroupBettingController.run(config)
