# import libraries
import pandas as pd
import csv
import numpy as np
import datetime
import time
import pickle
import json
import multiprocessing as mp
import concurrent.futures
import os
from tqdm import tqdm
from itertools import combinations
import random
import gc
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
# output1 = config.GetTemp1(config)
output2 = config.GetTemp2(config)
match_output = config.GetMatchOuput(config)
score_output = config.GetScoreOuput(config)
trans_output = config.GetTransOuput(config)
class ProcessMatchBased():
    def __init__(self,df,match,bet_type,league):
    # total_combination,order_of_combination):
        self.MATCH = df
        # self.major_league_list = major_league_list
        self.match = match
        self.bet_type = bet_type
        self.league = league
        # self.total_combination = total_combination
        # self.order_of_combination = order_of_combination
        # self.output1 = output1
        # self.output2 = output2
        # self.match_output = match_output
        
    
    # def construct_obj(self):

    def compute_time_score(self,trans_arr,time_arr,cus_arr):
        """
        >>> Input  :    array of transactions ID,
                        array of time points,
                        array of customers

        >>> Output :    time_score : a real number in range [0,1],
                        effective transactions ID : a set
        """ 
        
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
        
        return time_score,eff_trans


    def processing_a_match(self) :
        """
        DO PROCESSING FOR EVERY COUPLE IN A COMBINATION (MATCH,BETTYPE) !
        .
        .
        .
        >>> Output : (result_of_the_match,
                    effective transactions)
        """
        # os.mkdir(os.path.join('match',f'M{self.match}B{self.bet_type}'))
        eff_trans,couple_for_table_2 = set(),[]
        # pick up customer list
        self.cus_list = self.MATCH.custid.unique()

        print('\n')
        
        # loop through 1st customer
        for k in tqdm(range(len(self.cus_list)-1),desc=f"BET TYPE {self.bet_type} MATCH {self.match}"):
            cus_a = self.cus_list[k]
        
            # loop through 2nd customer
            for j in range(k+1,len(self.cus_list)):
                cus_b = self.cus_list[j]
                # get (transid,transdate) of customer b
                df = self.MATCH[self.MATCH.custid.isin([cus_a,cus_b])][['transid','transdate','custid']]

                transid,time_serie,custid = df['transid'].values,df['transdate'].values,df['custid'].values

                # compute time score, get labels, get valid clusters, get effective transid
                time_score,transid_set = self.compute_time_score(transid,time_serie,custid)
                # if (self.match == 37131066 or self.match == 37131288) and cus_a in [3560567, 4835843] and cus_b in [3560567, 4835843] :
                # transid = ','.join([str(trans) for trans in transid_set if trans !=])
                # if transid != '':
                #     print(f"TRANSID {transid}")
                # add effective transid to set
                # transid_list = transid_string.split(',')
                # for transid in transid_list:
                eff_trans = eff_trans.union(transid_set)
                
                # save a couple
                # if time_score > 0 : 
                # or self.league not in self.major_league_list:
                # couple_for_table_1 =    {
                #                         'bet_type':self.bet_type,
                #                         'CustID1':min(cus_a,cus_b),
                #                         'CustID2':max(cus_a,cus_b),                                                            
                #                         'TimeScore':time_score,
                #                         # 'MatchID':str(self.match),
                #                         'LeagueID':self.league,
                #                         'BETCount': len(transid),
                #                         # 'TransIdList': ','.join([str(trans) for trans in transid_set]),
                #                         # 'TotalSuspiciousTicktes':len(transid_set)                                                         
                #                         }
                # couple_for_table_1 = [self.bet_type,time_score,self.league,len(transid)]
                couple_for_table_2.append   ({
                                            'bet_type':self.bet_type,
                                            'CustID1':min(cus_a,cus_b),
                                            'CustID2':max(cus_a,cus_b),                                                            
                                            'TimeScore':time_score,
                                            'MatchID':str(self.match),
                                            'LeagueID':self.league,
                                            'BETCount': len(transid),
                                            'TransIdList': ','.join([str(trans) for trans in transid_set]),
                                            'TotalSuspiciousTicktes':len(transid_set)          
                                            })                  
                # file_name = str(couple[0]['CustID1'])+'_'+str(couple[0]['CustID2'])
                # file_name = str(min(cus_a,cus_b))+'_'+str(max(cus_a,cus_b))
                # if file_name in os.listdir(self.output):
                # with open(os.path.join(output1,file_name+'.csv'),'a') as csv_file:
                #     writer = csv.writer(csv_file)
                #     # if csv_file.shape[0] > 1:
                #     #     print("YAYYYY !")
                #     writer.writerow(couple_for_table_1)
                    # writer.writerow(couple_for_table_1.values())
                # else:
        #         print what makes you happy :)           
        #         if time_score == 1. and len(transid_set) > 4:
        #             print(f"BETTYPE {bet_type} MATCH {match} | CUS {cus_a} & CUS {cus_b} | TIME SCORE {time_score} | TRANSID {','.join([str(trans) for trans in transid_set])}") 
        # return result_of_the_match,eff_trans
        #             COUPLE = pd.DataFrame(couple)
        print(f"BETTYPE {self.bet_type} MATCH {self.match}",'********',RESULT.head(),sep='\n')
                    # COUPLE.to_csv(self.output+file_name+'.csv')
        with open(os.path.join(output2,f'B{self.bet_type}M{self.match}_eff_trans.pkl'),'wb') as f:
            pickle.dump(eff_trans,f)
        # with open(os.path.join(self.output2,f'B{self.bet_type}M{self.match}_detailed.pkl'),'wb') as g:
        #     pickle.dump(couple_for_table_2,g)
        TABLE2 = pd.DataFrame(couple_for_table_2)
        TABLE2.to_csv(os.path.join(match_output,f'B{self.bet_type}M{self.match}.csv'))
        del TABLE2,eff_trans,couple_for_table_2,couple_for_table_1
        gc.collect()
        
    # def process_a_couple(self,couple) :
    #     """
    #     DO PROCESSING FOR EVERY COUPLE IN A COMBINATION (MATCH,BETTYPE) !
    #     .
    #     .
    #     .
    #     >>> Output : (result_of_the_match,
    #                 effective transactions)
    #     """
    #     cus_a,cus_b = couple[0],couple[1]
    #     df = self.MATCH[self.MATCH.custid.isin([cus_a,cus_b])][['transid','transdate','custid']]

    #     transid,time_serie,custid = df['transid'].values,df['transdate'].values,df['custid'].values

    #     # compute time score, get labels, get valid clusters, get effective transid
    #     time_score,transid_set = self.compute_time_score(transid,time_serie,custid)
        
    #     couple_for_table_1 = [self.bet_type,time_score,self.league,len(transid)]
    #     couple_for_table_2 =   {
    #                                 # 'bet_type':self.bet_type,
    #                                 'CustID1':min(cus_a,cus_b),
    #                                 'CustID2':max(cus_a,cus_b),                                                            
    #                                 # 'TimeScore':time_score,
    #                                 'MatchID':str(self.match),
    #                                 'LeagueID':self.league,
    #                                 # 'BETCount': len(transid),
    #                                 'TransIdList': ','.join([str(trans) for trans in transid_set]),
    #                                 'TotalSuspiciousTicktes':len(transid_set)          
    #                             }                
    #     # file_name = str(couple[0]['CustID1'])+'_'+str(couple[0]['CustID2'])
    #     file_name = str(min(cus_a,cus_b))+'_'+str(max(cus_a,cus_b))
    #     # if file_name in os.listdir(self.output):
    #     if time_score > .75 and len(transid_set) >= 4:
    #         print("\n")
    #         print(f"CUS {cus_a} & CUS {cus_b} | TIME SCORE {time_score} | TRANSID {','.join([str(trans) for trans in transid_set])}")
    #     with open(os.path.join(self.output1,file_name+'.csv'),'a') as csv_file:
    #         writer = csv.writer(csv_file)
    #         # if csv_file.shape[0] > 1:
    #         #     print("YAYYYY !")
    #         writer.writerow(couple_for_table_1)
    #     return couple_for_table_2,transid_set
                    
    
    # def process_a_match_with_parallelism(self):
    #     # print("\n")
    #     # print(f"BETTYPE {self.bet_type} MATCH {self.match}","*********************************",sep='\n')
    #     eff_trans,couple_for_table_2 = set(),[]
    #     # pick up customer list
    #     self.cus_list = self.MATCH.custid.unique()
    #     couples = list(combinations(self.cus_list,2))
    #     # couples = combinations(self.cus_list,2)
    #     # num_batch = 10000
        
    #     pool = mp.Pool(processes=8)
    #     # for _ in tqdm(range(20000),desc=f"B {self.bet_type} M {self.match} {self.order_of_combination}/{self.total_combination} {len(self.cus_list)} CUSTOMERS"):
    #     #     t1 = [couples.pop(random.randrange(len(couples))) for _ in range(num_batch)]
    #     for _ in tqdm(  pool.imap_unordered(self.process_a_couple,couples[:100000]),total=len(couples[:100000]),
    #                     desc=f"B {self.bet_type} M {self.match} {self.order_of_combination}/{self.total_combination} {len(self.cus_list)} CUSTOMERS"):
    #         pass
    #     print(f"B {self.bet_type} M {self.match} {self.order_of_combination}/{self.total_combination} {len(self.cus_list)} CUSTOMERS","*********************************",sep='\n')
    #     with concurrent.futures.ProcessPoolExecutor() as executor:
    #         results = [executor.submit(self.process_a_couple,*couple) for couple in couples]
    #         executor.map(self.process_a_couple,couples)

    #         for f in concurrent.futures.as_completed(results):
    #             info_of_couple = f.result()[0]
    #             trans = f.result()[1]
    #             eff_trans = eff_trans.union(trans)
    #             couple_for_table_2.append(info_of_couple)

    #     with open(os.path.join(self.output2,f'B{self.bet_type}M{self.match}_eff_trans.pkl'),'wb') as f:
    #         pickle.dump(eff_trans,f)
        
    #     TABLE2 = pd.DataFrame(couple_for_table_2)
    #     TABLE2.to_csv(os.path.join(self.match_output,f'B{self.bet_type}M{self.match}.csv'))