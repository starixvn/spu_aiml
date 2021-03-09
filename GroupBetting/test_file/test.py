import numpy as np
from numba import prange, njit, set_num_threads, jit
from numba.typed import List
import numba
from pyunpack import Archive
import pandas as pd
import paramiko
import logging
import urllib.request
import csv
import os
import json
from mysql.connector import MySQLConnection
from Configuration.Configuration import Configuration
import requests
from tqdm import tqdm
config = Configuration()
save_dir_log =config.GetSaveDirectoryModel(config)
log_name = config.GetLogName(config)
logging.basicConfig(filename=os.path.join(save_dir_log,log_name),level=logging.DEBUG)

if __name__ == "__main__":
  #os.system('find /home/vnteam/Data/MatchData/match_breaking -type f -exec rm {} +;')
  os.system('source env/bin/activate')
  #a = "abc.csv"
  #os.remove(f"/home/vnteam/Data/SaveData/output1a/{a}")




    
  
    
    
