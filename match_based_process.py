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
import pandas as pd
from GroupBetting.InsertDataBase import InsertDataBase
from GroupBetting.ProcessMatchBased import ProcessMatchBased
from ReadData import ReadData
from GroupBetting.Aggregate import Aggregate
from Configuration.Configuration import Configuration
from pandarallel import pandarallel
config = Configuration()
# algorithmScore = FeatureScore()
# aggregate = AggregateDatabase()

# get information all ticket of each match
save_dir =config.GetSaveDirectoryModel(config)
path_csv = config.GetPathCsvFile(config)
filecsv_name = os.path.join(path_csv,config.GetNameFile(config))
name2 = os.path.join(path_csv,config.GetMajorLeagueName(config))
# log_name = config.GetLogName(config)
name1 = os.path.join(path_csv,config.GetMatchLeagueMapping(config))
output1a = os.path.join(save_dir,config.GetTemp1A(config))
# output1 = config.GetTemp1(config)
output2 = os.path.join(save_dir,config.GetTemp2(config))
match_output = os.path.join(save_dir,config.GetMatchOuput(config))
# match_output = config.GetMatchOuput(config)
# score_output = config.GetScoreOuput(config)
file_output = os.path.join(save_dir,config.GetFileOutput(config))
# process_start_time = time.time()

match_league_map = pd.read_csv(name1,error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
# def submit_job(args):

# def submit_job(fn):

  # ns,k = args[0],args[1]
  # total_combination = len(ns.ls)
  # combinations = ns.ls

  # (match,bet_type) = int(fn.split('.')[0].split('_')[0]),int(fn.split('.')[0].split('_')[1])
  # DF = pd.read_csv(os.path.join(file_output,fn))
  # league = match_league_map[match]['leagueid']
  # objlv2 = ProcessMatchBased  (df=DF,
  #                             match=match,bet_type=bet_type,league=league)
                              # total_combination=5124,order_of_combination=k+1)
  
  # objlv2.processing_a_match()
  # objlv2.process_a_match_with_parallelism()

match,bettype=39570459,1
data=pd.read_csv(os.path.join(file_output,str(match)+'_'+str(bettype)+'.csv'))
ls=data.custid.unique()

def processing(args):
  def compute_time_score(triple):
      """
      >>> Input  :    array of transactions ID,
                      array of time points,
                      array of customers

      >>> Output :    time_score : a real number in range [0,1],
                      effective transactions ID : a set
      """ 
      cus_arr,trans_arr,time_arr = triple[:,0],triple[:,1],triple[:,2]
      diff_time = time_arr[1:]-time_arr[:-1]
      diff_cus = cus_arr[1:]-cus_arr[:-1]
      zip_trans = np.column_stack((trans_arr[1:],trans_arr[:-1]))
      
      eff_trans = zip_trans[(diff_cus != 0) & (diff_time <= 20)]
      fil_cus_tickets = diff_time[diff_cus != 0]
      fil_time_tickets = fil_cus_tickets[fil_cus_tickets <= 20]
      if len(fil_time_tickets)==0:
          time_score = 0
      else:
          time_score = (20-np.mean(fil_time_tickets)) / 20

      eff_trans = set(eff_trans.flatten())
      if len(eff_trans) == 0:
          eff_trans = ''
      
      return (time_score,','.join([str(x) for x in eff_trans]))
  
  def compute_league_score(list_minor=None,list_major=None):
      """"
      >>> Input  : list of minor leagues,list of major leagues

      >>> Output : league_score
      """
      def gini_score(lista):
          """
          >>> Input  : list of integer,each represents quantity of some class
          >>> Output : gini score
          ------------------------
          Example

          > Input  : [1,1]
          > Output : .5
          """
          sum_match = sum(lista)

          return 1 - sum(map(lambda x:(x/sum_match)**2,lista))
      
      gini_minor = gini_score(list_minor)
      gini_major = gini_score(list_major)
      if len(list_minor) == 0:
          league_score = (gini_major + 3/2) * (2/5)
      elif len(list_major) == 0:
          league_score = (gini_minor + 5/2) * (2/7)
      else:
          minor_score = (gini_minor + 5/2) * (2/7)
          major_score = (gini_major + 3/2) * (2/5)
          league_score = (3 * (minor_score + 1) + (major_score + 2)) * (1/9)
      return league_score

  (k,j)=args
  
  df = data[data.custid.isin([cus_a,cus_b])][['transid','transdate','custid']]

  transid,time_serie,custid = df['transid'].values,df['transdate'].values,df['custid'].values

  # compute time score, get labels, get valid clusters, get effective transid
  time_score,transid_set = compute_time_score(transid,time_serie,custid)
  return  {
          'bet_type':self.bet_type,
          'CustID1':min(cus_a,cus_b),
          'CustID2':max(cus_a,cus_b),                                                            
          'TimeScore':time_score,
          'MatchID':str(self.match),
          'LeagueID':self.league,
          'BETCount': len(transid),
          'TransIdList': ','.join([str(trans) for trans in transid_set]),
          'TotalSuspiciousTicktes':len(transid_set)          
          }              
        
  # print(f"BETTYPE {self.bet_type} MATCH {self.match}",'********',RESULT.head(),sep='\n')
              # COUPLE.to_csv(self.output+file_name+'.csv')
  # with open(os.path.join(output2,f'B{bettype}M{match}_eff_trans.pkl'),'wb') as f:
  #     pickle.dump(eff_trans,f)
  # with open(os.path.join(self.output2,f'B{self.bet_type}M{self.match}_detailed.pkl'),'wb') as g:
  #     pickle.dump(couple_for_table_2,g)
  # with open(os.path.join(output1a,f"M{match}_B{bettype}.json"),"w") as f:
    # json.dump(couple_for_table_2,f)
  # del TABLE2,eff_trans,couple_for_table_2,couple_for_table_1
  # gc.collect()


if __name__ == "__main__":

  start_time = time.time()

  pandarallel.initialize()
  # i=0
  # import swifter
  myls=[]
  # start=time.time()
  for k in tqdm(range(len(ls)-1),desc="Overall Progress"):
  # for k in range(6):
      for j in range(k+1,len(ls)):
          # i += 1
          myls.append((k,j))
          # if i == 1e5:
          # print("INSERT TIME %.0f seconds" % (time.time()-start))
      # start=time.time()
      mysr=pd.Series(myls)
      # mylady=mysr.parallel_apply(processing)
      mylady=mysr.progress_apply(processing)
      # mylady=mysr.swifter.set_npartitions(mp.cpu_count()).apply(processing)
      filtered=mylady[mylady != '']
      list_of_dict=filtered.to_list()
      del myls,mysr,mylady,filtered
      with open(os.path.join(output1a,f"{k}.json"),"w") as f:
          json.dump(list_of_dict,f)
              # print("APPLY TIME %.0f seconds" % (time.time()-start))
              # i,myls=0,[]
      del list_of_dict
      gc.collect()
      # print("Loop %.0f takes %.0f seconds" % (k+1,time.time()-start))
      myls=[]
  # pool = mp.Pool(8)
  # pool.map(submit_job,[(ns,k) for k in range(K)])
  # pool.map(submit_job,os.listdir(file_output))

  
  print("***********************************************************************************************************************************************************************************")
  print("TOTAL IMPLEMENTATION TIME %.0f SECONDS" % (time.time() - start_time))


# mkdir output1 output2 score_output trans_output match_output
# rm -r output1 output2 score_output trans_output match_output