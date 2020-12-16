# import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np
from tqdm import tqdm
import time
import csv
import multiprocessing as mp
import concurrent.futures
import os
import pickle
import pandas as pd
from GroupBetting.ProcessCusBased import ProcessCusBased
#from GroupBetting import ReadData
from GroupBetting.Aggregate import Aggregate
from GroupBetting.InsertDataBase import InsertDataBase
from Configuration.Configuration import Configuration
#from customer_based_process import objlv1

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
# objlv1 = ReadData()
# objlv1.read_data(filecsv_name,name1,name2)
# objlv1.pre_process()



def agg(file_name):

#   for file_name in tqdm(os.listdir(output1),desc='AGGREGATING. . .'):
    objlv3 = Aggregate(file_name,score_output,output1)
    objlv3.aggregate(objlv1.major_league_list)
#   print('\n')
  # print(f"START ")

def insert():
    trans = set()
    for file_name in tqdm(os.listdir(output2),desc='INSERTING. . .'):
        if 'eff_trans' in file_name:
            with open(os.path.join(output2,file_name),'rb') as f:
                eff_trans = pickle.load(f)
                # print(f"EFF TRANS {eff_trans} | TYPE {type(eff_trans)}")
                trans = trans.union(eff_trans)
    objlv4 = InsertDataBase(trans)
    objlv4.insert_transactions(objlv1.data,trans_output)


if __name__ == "__main__":

  start_time = time.time()
  

#   with concurrent.futures.ThreadPoolExecutor() as executor:
          # results = [executor.submit(self.process_a_couple,*couple) for couple in couples]
    # executor.map(submit_job,[(cus_list[k],cus_list[k+1:]) for k in range(len(cus_list)-1)])

  pool = mp.Pool(processes=8)
  #     # for _ in tqdm(range(20000),desc=f"B {self.bet_type} M {self.match} {self.order_of_combination}/{self.total_combination} {len(self.cus_list)} CUSTOMERS"):
  #     #     t1 = [couples.pop(random.randrange(len(couples))) for _ in range(num_batch)]
  for _ in tqdm(    pool.imap_unordered(agg,os.listdir(output1)),total=len(os.listdir(output1)),
                    desc='AGGREGATING. . .'):
    pass
  
  insert()
  
  print("***********************************************************************************************************************************************************************************")
  print("AGG & INSERT TIME %.0f SECONDS" % (time.time() - start_time))