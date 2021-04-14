from Configuration.Configuration import Configuration
ENV='LOCAL'
if ENV=='LOCAL':
    config = Configuration("localconfig.ini",ENV)
else:
    config = Configuration("proconfig.ini",ENV)
import pandas as pd
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
import logging
import csv
import re
import json
import warnings
from DataAccess.GroupBettingDA.SPU_AIML import AssociationStatsStaging
from TaskManagement.GroupBettingManagement import main
#from DataAccess.CommonDA import SystemParameter
#from GroupBetting.MainJobs import AggDayEnd
#from GroupBetting.MainJobs import AggOnTheFly
#from GroupBetting.MainJobs import GroupbyIP
#from GroupBetting.MainJobs import Prepare_DataTS

#from GroupBetting.Support import helper
#from GroupBetting.Support import SendLogTelegram
import datetime
import time
import pickle
import itertools
import gc
import os
import torch

from tqdm import tqdm
#from pandarallel import pandarallel
# from sklearn.metrics import pairwise_distances
from mysql.connector import MySQLConnection


from datetime import date as dt
from datetime import timedelta

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
    
    
