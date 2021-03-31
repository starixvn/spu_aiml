import pandas as pd
import numpy as np
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor,as_completed
import logging
import csv
import json
import warnings
from GroupBetting import helper
from GroupBetting import SendLogTelegram
# import SendLogTelegram
# import agg
import datetime
import time
import pickle
import itertools
import gc
import os
import torch

from tqdm import tqdm
# from pandarallel import pandarallel
# from sklearn.metrics import pairwise_distances
from mysql.connector import MySQLConnection
from Configuration.LocalConfiguration import LocalConfiguration
from Configuration.ProConfiguration import ProConfiguration
from datetime import date as dt
from datetime import timedelta

warnings.filterwarnings("ignore")

ENV='LOCAL'

if ENV=='LOCAL':

    config = LocalConfiguration()

    # define log config
    save_dir_log = config.GetSaveDirectoryLog(config)
    log_name = config.GetLogName(config)
    logging.basicConfig(filename=os.path.join(
        save_dir_log, log_name), level=logging.INFO)

    # define GroupBetting config
    config_retry = int(config.getRetry(config))
    time_sleep = int(config.getTimeSleep(config))
    percent_score = int(config.getPercentScore(config))
    time_threshold = int(config.GetTimeThreshold(config))
    combination_threshold = int(config.GetCombinationThreshold(config))
    # define paths
    # root = "/home/vnteam/Data/MatchData/"
    root=config.GetSaveDataDir(config)
    # root_orig = "/home/vndata4ai/"
    root_orig=config.GetPathCsvFile(config)
    # orig_fn="bettrans_01_31_2021.csv"
    orig_fn=config.GetNameFile(config)
    match_breaking=config.GetMatchBreaking(config)
    # cus_list_fn = 'cus_list.pkl'
    cus_list_fn=config.GetListName(config)
    # cus_dict_fn = 'cus_dict.pkl'
    cus_dict_fn=config.GetDictName(config)
    # mlm_dict_fn = 'match_league_map.pkl'
    mlm_dict_fn=config.GetMatchLeagueMap(config)
    backup=config.GetBackUp(config)

    # define chunk_size for DB saving
    chunk_size = int(config.getChunkSize(config))

    # define nb_workers_phase_1
    nb_workers_phase_1 = int(config.getNumberWorkerPhase1(config))

    # define nb_workers_phase_2
    nb_workers_phase_2 = int(config.getNumberWorkerPhase2(config))

    aimluser=config.getSPU_AIMLUsername(config)
    aimlpwd=config.getSPU_AIMLPassword(config)
    aimlhost=config.getSPU_AIMLHost(config)
    aimlport=config.getSPU_AIMLPort(config)
    aimldb=config.getSPU_AIMLDatabaseName(config)

    ctsuser=config.getCTS_DataCenterUsername(config)
    ctspwd=config.getCTS_DataCenterPassword(config)
    ctshost=config.getCTS_DataCenterHost(config)
    ctsport=config.getCTS_DataCenterPort(config)
    ctsdb=config.getCTS_DataCenterDatabaseName(config)
else:
    config = ProConfiguration()

    # define log config
    save_dir_log = config.GetSaveDirectoryLog(config)
    log_name = config.GetLogName(config)
    logging.basicConfig(filename=os.path.join(
        save_dir_log, log_name), level=logging.INFO)

    # define GroupBetting config
    config_retry = int(config.getRetry(config))
    time_sleep = int(config.getTimeSleep(config))
    percent_score = int(config.getPercentScore(config))
    time_threshold = int(config.GetTimeThreshold(config))
    combination_threshold = int(config.GetCombinationThreshold(config))
    # define paths
    # root = "/home/vnteam/Data/MatchData/"
    root=config.GetSaveDataDir(config)
    # root_orig = "/home/vndata4ai/"
    root_orig=config.GetPathCsvFile(config)
    # orig_fn="bettrans_01_31_2021.csv"
    orig_fn=config.GetNameFile(config)
    match_breaking=config.GetMatchBreaking(config)
    # cus_list_fn = 'cus_list.pkl'
    cus_list_fn=config.GetListName(config)
    # cus_dict_fn = 'cus_dict.pkl'
    cus_dict_fn=config.GetDictName(config)
    # mlm_dict_fn = 'match_league_map.pkl'
    mlm_dict_fn=config.GetMatchLeagueMap(config)
    backup=config.GetBackUp(config)

    # define chunk_size for DB saving
    chunk_size = int(config.getChunkSize(config))

    # define nb_workers_phase_1
    nb_workers_phase_1 = int(config.getNumberWorkerPhase1(config))

    # define nb_workers_phase_2
    nb_workers_phase_2 = int(config.getNumberWorkerPhase2(config))

    aimluser=config.getSPU_AIMLUsername(config)
    aimlpwd=config.getSPU_AIMLPassword(config)
    aimlhost=config.getSPU_AIMLHost(config)
    aimlport=config.getSPU_AIMLPort(config)
    aimldb=config.getSPU_AIMLDatabaseName(config)

    ctsuser=config.getCTS_DataCenterUsername(config)
    ctspwd=config.getCTS_DataCenterPassword(config)
    ctshost=config.getCTS_DataCenterHost(config)
    ctsport=config.getCTS_DataCenterPort(config)
    ctsdb=config.getCTS_DataCenterDatabaseName(config)


  

if __name__ == "__main__":

    conn = MySQLConnection(user=aimluser, password=aimlpwd,
                            host=aimlhost, port=aimlport, database=aimldb)
    cur = conn.cursor()
    # Truncate table AssociationStatsStaging
    # cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
    #             ['AssociationStatsStaging'])
    # cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
    #             ['AssociationSuspiciousInfo'])
    cur.callproc('SPU_AIML.SPU_AIML_DBA_Truncate_Table',
                ['AssociationByAI'])
    conn.commit()