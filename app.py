import logging
import os
import warnings

from Configuration.Configuration import config
from DataAccess.GroupBettingDA.SPU_AIML.AssociationStatsStaging import AssociationStatsStagingDA
from GroupBettingController import main

warnings.filterwarnings("ignore")
logging.basicConfig(filename=os.path.join(config.save_dir_log, config.log_name), level=logging.INFO)


if __name__ == "__main__":
    #region Clear and Clean Data
    association_stats_staging_da = AssociationStatsStagingDA()

    association_stats_staging_da.truncate()
    check_cus_files=os.listdir(config.root)
    if config.cus_list_fn in check_cus_files:
        os.remove(os.path.join(config.root,config.cus_list_fn))
    if config.cus_dict_fn in check_cus_files:
        os.remove(os.path.join(config.root,config.cus_dict_fn))
    
    main.run(config)
    
    
