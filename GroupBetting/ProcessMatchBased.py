import pandas as pd
import pickle
import numpy as np
import csv
import datetime
import time
import os
from tqdm import tqdm

class Processing():
    """description of class"""
    def __init__(self,df,match,bet_type,league,total_combination,order_of_combination,output1,output2,match_output):
        self.MATCH = df
        # self.major_league_list = major_league_list
        self.match = match
        self.bet_type = bet_type
        self.league = league
        self.total_combination = total_combination
        self.order_of_combination = order_of_combination
        self.output1 = output1
        self.output2 = output2
        self.match_output = match_output

    def compute_time_score(self, trans_arr, time_arr, cus_arr):
        """
        >>> Input  : array of transactions ID,
                    array of time points,
                    array of customers

        >>> Output : time_score : a real number in range [0,1],
                    transactions ID : a list
        """

        diff_time = time_arr[1:] - time_arr[:-1]
        diff_cus = cus_arr[1:] - cus_arr[:-1]
        zip_trans = np.column_stack((trans_arr[1:], trans_arr[:-1]))
        eff_trans = zip_trans[(diff_cus != 0) & (diff_time <= 20)]
        fil_cus_tickets = diff_time[diff_cus != 0]
        fil_time_tickets = fil_cus_tickets[fil_cus_tickets <= 20]
           
        if len(fil_time_tickets) == 0:
            time_score = 0
        else:
            time_score = (20 - np.mean(fil_time_tickets)) / 20
        eff_trans = set(eff_trans.flatten())
        if len(eff_trans) == 0:
            eff_trans = ''
        
        return time_score,eff_trans
        # return time_score, list(set(eff_trans.flatten()))


    def processing_a_match(self):
        """
        >>> Input  : (match,bet_type)
        .
        .
        .
        DO PROCESSING !
        .
        .
        .
        >>> Output : (feautes_for_each_couple,
                    their effective transaction)
        """

        # match = args[0][0]
        # bet_type = args[0][1]
        # matches_live = args[1]
        # result_of_the_match = []
        # eff_trans = set()

        # league = matches_live.leagueid.unique()[0]
        # matches_data = matches_live[(matches_live.bettype == bet_type) & (matches_live.matchid == match)]

        # os.mkdir(os.path.join('match',f'M{self.match}B{self.bet_type}'))
        eff_trans,couple_for_table_2 = set(),[]
        # pick up customer list
        self.cus_list = self.MATCH.custid.unique()

        print('\n')

        # pick up customer list
        # cus_list = matches_data.custid.unique()

        # loop through 1st customer
        for k in tqdm(range(len(self.cus_list)-1),desc=f"BET TYPE {self.bet_type} MATCH {self.match} {self.order_of_combination}/{self.total_combination}"):
            cus_a = self.cus_list[k]
            #transid_transdate_a = matches_data[matches_data.custid == cus_a][['transid','transdate']].values

            # loop through 2st customer
            for j in range(k+1, len(self.cus_list)):
                cus_b = self.cus_list[j]
                #transid_transdate_b = matches_data[matches_data.custid == cus_b][['transid','transdate']].values
                df = self.MATCH[self.MATCH.custid.isin([cus_a, cus_b])][['transid', 'transdate', 'custid']]

                # compute time score, get labels, get valid clusters, get effective transid
                #time_score, labels, valid_cluster_list, transid_string = compute_difference(transid_transdate_a, transid_transdate_b)

                # add effective transid to set
                # transid_list = transid_string.split(',')
                # for transid in transid_list:
                #     eff_trans.add(transid)

                transid = df['transid'].values
                time_serie = df['transdate'].values
                custid = df['custid'].values

                time_score, transid_set = self.compute_time_score(transid, time_serie, custid)
                eff_trans = eff_trans.union(transid_set)

                # save a couple
                couple_for_table_1 = [self.bet_type,time_score,self.league,len(transid)]
                couple_for_table_2.append   ({
                                            # 'bet_type':self.bet_type,
                                            'CustID1':min(cus_a,cus_b),
                                            'CustID2':max(cus_a,cus_b),                                                            
                                            # 'TimeScore':time_score,
                                            'MatchID':str(self.match),
                                            'LeagueID':self.league,
                                            # 'BETCount': len(transid),
                                            'TransIdList': ','.join([str(trans) for trans in transid_set]),
                                            'TotalSuspiciousTicktes':len(transid_set)          
                                            })                  
                # file_name = str(couple[0]['CustID1'])+'_'+str(couple[0]['CustID2'])
                file_name = str(min(cus_a,cus_b))+'_'+str(max(cus_a,cus_b))
                # if file_name in os.listdir(self.output):
                with open(os.path.join(self.output1,file_name+'.csv'),'a') as csv_file:
                    writer = csv.writer(csv_file)
                    # if csv_file.shape[0] > 1:
                    #     print("YAYYYY !")
                    writer.writerow(couple_for_table_1)
                
                # print what makes you happy
                if time_score >= .9 and len(transid_set) > 4:
                    print(f"BETTYPE {bet_type} MATCH {match} | CUS {cus_a} & CUS {cus_b} | TIME SCORE {time_score} | TRANSID {','.join([str(trans) for trans in transid_set])}")

        with open(os.path.join(self.output2,f'B{self.bet_type}M{self.match}_eff_trans.pkl'),'wb') as f:
            pickle.dump(eff_trans,f)
        # with open(os.path.join(self.output2,f'B{self.bet_type}M{self.match}_detailed.pkl'),'wb') as g:
        #     pickle.dump(couple_for_table_2,g)
        TABLE2 = pd.DataFrame(couple_for_table_2)
        TABLE2.to_csv(os.path.join(self.match_output,f'B{self.bet_type}M{self.match}.csv'))

