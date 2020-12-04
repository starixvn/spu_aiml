import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import datetime
import time
from sklearn.cluster import DBSCAN
from tqdm import tqdm

class FeatureScore():
    """description of class"""
    def __init__(self, *args):
        pass

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
        return time_score, list(set(eff_trans.flatten()))

    def gini_score(self, lista):
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

    def compute_league_score(self, list_minor = None, list_major = None):
        """"
        >>> Input  : list_minor, list of number of match in minor league
                    list_major, list of number of match in major league

        >>> Output : league_score
        """
        gini_minor = self.gini_score(list_minor)
        gini_major = self.gini_score(list_major)
        if len(list_minor) == 0:
            league_score = (gini_major + 3/2) * (2/5)
        elif len(list_major) == 0:
            league_score = (gini_minor + 5/2) * (2/7)
        else:
            minor_score = (gini_minor + 5/2) * (2/7)
            major_score = (gini_major + 3/2) * (2/5)
            league_score = (3 * (minor_score + 1) + (major_score + 2)) * (1/9)
        return league_score


    def separate(self, transdate):
        """
        >>> Input  : '2020-09-26 7:31:01.872'

        >>> Output : (2020,9,26,7,31,1)
        """
        date,hms = transdate.split(' ')[0].split('-'),transdate.split(' ')[1].split('.')[0].split(':')
        year,month,day = int(date[0]),int(date[1]),int(date[2])
        hour,min,sec = int(hms[0]),int(hms[1]),int(hms[2])
        return (year,month,day,hour,min,sec)

    def distance_time(self, transdate1, transdate2):
        """
        >>> Input  : transdate 1 : (2020,9,26,7,28,1)

                    transdate 2 : (2020,9,26,7,31,1)

        >>> Output : 180 seconds
        """
  
        a = datetime.datetime(*transdate1)
        b = datetime.datetime(*transdate2)
        c = b-a
        return c.total_seconds()

    def do_something(self, seconds):
        print(f'Sleeping {seconds} second(s)...')
        time.sleep(seconds)
        return 'Done Sleeping...'
    

    def calculateTotalScore(self, args):
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

        match = args[0][0]
        bet_type = args[0][1]
        matches_live = args[1]
        result_of_the_match = []
        eff_trans = set()

        league = matches_live.leagueid.unique()[0]
        matches_data = matches_live[(matches_live.bettype == bet_type) & (matches_live.matchid == match)]

        # pick up customer list
        cus_list = matches_data.custid.unique()

        if len(cus_list) < 2:
            print('\n')
            print(f"BET TYPE {bet_type} MATCH {match} NOT ENOUGH !")
            print('\n')
        else:
            print('\n')
            print(f"BET TYPE {bet_type} MATCH {match} HAVING {len(cus_list)} CUSTOMERS STARTS RUNNING !")
            print('\n')

            # loop through 1st customer
            for k in tqdm(range(len(cus_list) - 1),desc=f'BET TYPE {bet_type} MATCH {match}'):
                cus_a = cus_list[k]
                #transid_transdate_a = matches_data[matches_data.custid == cus_a][['transid','transdate']].values

                # loop through 2st customer
                for j in range(k+1, len(cus_list)):
                    cus_b = cus_list[j]
                    #transid_transdate_b = matches_data[matches_data.custid == cus_b][['transid','transdate']].values
                    df = matches_data[matches_data.custid.isin([cus_a, cus_b])][['transid', 'transdate', 'custid']]

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
                    eff_trans.union(transid_set)

                    # save a couple
                    result_of_the_match.append(
                        {
                            'bet_type': bet_type,
                            'couple': (min(cus_a,cus_b), max(cus_a,cus_b)),
                            'time_score': time_score,
                            'match':str(match),
                            'league': league,
                            'bet_count': len(transid),
                            'transid': ','.join([str(trans) for trans in transid_set])
                        }
                        )
                    
                    # print what makes you happy
                    if time_score >= .9 and len(transid_set) > 4:
                        print(f"BETTYPE {bet_type} MATCH {match} | CUS {cus_a} & CUS {cus_b} | TIME SCORE {time_score} | TRANSID {','.join([str(trans) for trans in transid_set])}")

            print('\n')
            print(f"BETTYPE {bet_type} MATCH {match} DONE !")
            print("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
            print('\n')
        return (result_of_the_match, eff_trans)

