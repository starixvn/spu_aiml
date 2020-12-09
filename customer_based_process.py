# import libraries
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
from GroupBetting.ReadData import ReadData
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
objlv1 = ReadData()
objlv1.read_data(filecsv_name,name1,name2)
objlv1.pre_process()
# cus_list = objlv1.DATE.custid.unique()
# print(f"NUMBER CUSTOMERS {len(cus_list)}")


# for bet_type in [1]:
DF = objlv1.DATE
cus_list = DF.custid.unique()

def submit_job(args):
    objlv2 = ProcessCusBased()
    cus_a,list_cus_b = args[0],args[1]
    match_a = set(DF[DF.custid==cus_a].matchid.unique())
    bettype_a = set(DF[DF.custid==cus_a].bettype.unique())
    couple_for_table_2,eff_trans = [],set()    
    # loop through 2nd customer
    print("\n")
    for j in tqdm(range(len(list_cus_b)),desc=f'LIST CUS B {len(list_cus_b)}'):
        cus_b = list_cus_b[j]
        
        # df_b = objlv1.DATE[objlv1.DATE.custid==cus_b]
        match_b = set(DF[DF.custid==cus_b].matchid.unique())
        bettype_b = set(DF[DF.custid==cus_b].bettype.unique())

        # find list of joining matches
        intersection_match = objlv2.find_intersection(match_a,match_b)
        intersection_bettype = objlv2.find_intersection(bettype_a,bettype_b)
    

        # filter
        if len(intersection_match)*len(intersection_bettype) > 0 :
        
            # loop through joining matches 
            for match in intersection_match:

                print(f"MATCH {match}")
        
                
                

                for bet_type in intersection_bettype:

                    df = DF[ (DF.custid.isin([cus_a,cus_b])) & (DF.matchid==match) & (DF.bettype==bet_type) ][['transid','transdate','custid','leagueid']]

                    league = df.leagueid.unique()[0]

                    if df.custid.nunique() > 1:

                      transid,time_serie,custid = df['transid'].values,df['transdate'].values,df['custid'].values

                      # compute time score, get labels, get valid clusters, get effective transid
                      time_score,transid_set = objlv2.compute_time_score(transid,time_serie,custid)
                      eff_trans = eff_trans.union(transid_set)

                      # save a couple
                      couple_for_table_2.append   (
                                                  {
                                                  # 'bet_type':bet_type,
                                                  'CustID1':min(cus_a,cus_b),
                                                  'CustID2':max(cus_a,cus_b),                                                            
                                                  # 'TimeScore':time_score,
                                                  'MatchID':match,
                                                  'LeagueID':league,
                                                  # 'BETCount': len(transid)
                                                  'TransIdList': ','.join([str(trans) for trans in transid_set]),
                                                  'TotalSuspiciousTicktes':len(transid_set)                                                         
                                                  }
                                                  )    
                      # couple_for_table_1 = [1,time_score,league,len(transid)]
                      couple_for_table_1 = [bet_type,time_score,league,len(transid)]

                      # couple_for_table_1.append   ({
                                                  # 'bet_type':self.bet_type,
                                                  # 'CustID1':min(cus_a,cus_b),
                                                  # 'CustID2':max(cus_a,cus_b),                                                            
                                                  # 'TimeScore':time_score,
                                                  # 'MatchID':str(self.match),
                                                  # 'LeagueID':self.league,
                                                  # 'BETCount': len(transid)
                                                  # 'TransIdList': ','.join([str(trans) for trans in transid_set]),
                                                  # 'TotalSuspiciousTicktes':len(transid_set)          
                                                  # })                  
                      # file_name = str(couple[0]['CustID1'])+'_'+str(couple[0]['CustID2'])
                      file_name = str(min(cus_a,cus_b))+'_'+str(max(cus_a,cus_b))
                      # if file_name in os.listdir(self.output):
                      with open(os.path.join(output1,file_name+'.csv'),'a') as csv_file:
                          writer = csv.writer(csv_file)
                          writer.writerow(couple_for_table_1)
           
      
    if couple_for_table_2 != []:
        with open(os.path.join(output2,f'{cus_a}_eff_trans.pkl'),'wb') as f:
            pickle.dump(eff_trans,f)
        TABLE2 = pd.DataFrame(couple_for_table_2)
        TABLE2.to_csv(os.path.join(match_output,str(cus_a)+'.csv'))
        del TABLE2,couple_for_table_2,eff_trans
    else:
        pass



if __name__ == "__main__":

  start_time = time.time()
  

  with concurrent.futures.ProcessPoolExecutor() as executor:
          # results = [executor.submit(self.process_a_couple,*couple) for couple in couples]
    executor.map(submit_job,[(cus_list[k],cus_list[k+1:]) for k in range(len(cus_list)-1)])

  # pool = mp.Pool(processes=8)
  #     # for _ in tqdm(range(20000),desc=f"B {self.bet_type} M {self.match} {self.order_of_combination}/{self.total_combination} {len(self.cus_list)} CUSTOMERS"):
  #     #     t1 = [couples.pop(random.randrange(len(couples))) for _ in range(num_batch)]
  # for _ in tqdm(  pool.imap_unordered(submit_job,[(cus_list[k],cus_list[k+1:]) for k in range(len(cus_list)-1)]),total=len(cus_list),
  #                     desc=f"BETTYPE 1"):
  #   pass
  
#   agg(output1,output2,score_output,trans_output,match_output)
  
  print("***********************************************************************************************************************************************************************************")
  print("PROCESS TIME %.0f SECONDS" % (time.time() - start_time))


    