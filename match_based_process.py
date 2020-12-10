# import libraries
# import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np
from tqdm import tqdm
import time
import argparse
import multiprocessing as mp
import concurrent.futures
import os
import pickle
from GroupBetting.InsertDataBase import InsertDataBase
from GroupBetting.ProcessMatchBased import ProcessMatchBased
from ReadData import ReadData
from GroupBetting.Aggregate import Aggregate
from Configuration.Configuration import Configuration

config = Configuration()
# algorithmScore = FeatureScore()
# aggregate = AggregateDatabase()

# get information all ticket of each match
# save_dir =config.GetSaveDirectoryModel(config)
path_csv = config.GetPathCsvFile(config)
filecsv_name = os.path.join(path_csv,config.GetNameFile(config))
name2 = os.path.join(path_csv,config.GetMajorLeagueName(config))
# log_name = config.GetLogName(config)
name1 = os.path.join(path_csv,config.GetMatchLeagueMapping(config))
output1 = config.GetTemp1(config)
output2 = config.GetTemp2(config)
match_output = config.GetMatchOuput(config)
score_output = config.GetScoreOuput(config)
trans_output = config.GetTransOuput(config)
# process_start_time = time.time()


def submit_job(args):

  ns,k = args[0],args[1]
  total_combination = len(ns.ls)
  # combinations = ns.ls
  (match,bet_type) = ns.ls[k]
  DF = ns.df
  league = ns.map[match]['leagueid']
  objlv2 = ProcessMatchBased  (df=DF[(DF.matchid==match)&(DF.bettype==bet_type)],
                              match=match,bet_type=bet_type,league=league,total_combination=total_combination,order_of_combination=k+1)
  
  objlv2.processing_a_match()
  # objlv2.process_a_match_with_parallelism()



if __name__ == "__main__":

  start_time = time.time()

  objlv1 = ReadData()
  objlv1.read_data(filecsv_name,name1,name2)
  objlv1.pre_process()
  # pick up match list
  matches = objlv1.DATE.matchid.unique()
  print(f"number of matches {len(matches)}")
  bet_type_list = objlv1.DATE.bettype.unique()
  print(f"number of bettype {len(bet_type_list)}")
  candidat = objlv1.DATE.groupby(['matchid','bettype']).custid.nunique()
  my_list = candidat[candidat>1].index.values
  # for match in matches:
  #     for bet_type in bet_type_list:
  #         my_list.append((match,bet_type))
  print(f"NUMBER COMBINATIONS {len(my_list)}")
  # cus_list = objlv1.DATE.custid.unique()
  K = len(my_list)
  mgr = mp.Manager()
  ns = mgr.Namespace()
  ns.df = objlv1.DATE
  ns.ls = my_list
  ns.map = objlv1.match_league_map
  # ns.support =  ProcessMatchBased()
  # q = mgr.Queue()
  # processes = []
  # for k in range(K-1):
  #     p=mp.Process(target=submit_job, args=(ns,k))
  #     processes.append(p)
  # for process in processes:
  #     process.start()
  # for process in processes:
  #     process.join()
  # q.put(objlv1,cus_list)
  # objlv1 = q.get()
  pool = mp.Pool(8)
  pool.map(submit_job,[(ns,k) for k in range(K)])

  
  print("***********************************************************************************************************************************************************************************")
  print("TOTAL IMPLEMENTATION TIME %.0f SECONDS" % (time.time() - start_time))


# mkdir output1 output2 score_output trans_output match_output
# rm -r output1 output2 score_output trans_output match_output