# import libraries
import pandas as pd
import numpy as np
from sklearn.metrics import pairwise_distances
import multiprocessing as mp
from mysql.connector import MySQLConnection
# from tqdm.notebook import tqdm
from tqdm import tqdm
import csv
import concurrent.futures as cf
import time
import datetime
import os
import json
import gc
import pickle
from GroupBetting.ProcessCusBased import ProcessCusBased
from Configuration.Configuration import Configuration
import itertools
from scipy.special import binom
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
output1a = config.GetTemp1A(config)
# output1b = config.GetTemp1B(config)
# output2 = config.GetTemp2(config)
# match_output = config.GetMatchOuput(config)
# score_output = config.GetScoreOuput(config)
# trans_output = config.GetTransOuput(config)
dict_name = config.GetDictName(config)

match_league_map = pd.read_csv(name1,error_bad_lines=False)[['matchid','leagueid']].set_index('matchid').to_dict(orient='index')
MAJOR_LEAGUE = pd.read_csv(name2)
major = MAJOR_LEAGUE.LeagueId.unique()
# # save_dict="dict_output"

with open(os.path.join(path_csv,dict_name), 'rb') as f:
    big_data=pickle.load(f)
print(f"NUM CUS {len(big_data)}","*****************************",sep='\n')

ls=list(big_data.keys())

# total_couples=int(binom(len(ls),2))
# print(f"TOTAL COUPELS {total_couples}")
# tasks=itertools.combinations([k for k in range(len(ls))],2)
# mgr = mp.Manager()
# ns = mgr.Namespace()
# ns.big_data=big_data
# ns.ls=ls
# ns.match_league_map=match_league_map
# ns.major=major

class Manager():
    def __init__(self,mlm,major,cd,cl):
        self.mlm = mlm
        # MAJOR_LEAGUE = pd.read_csv(name2)
        self.major = major
        self.cd=cd
        self.cl=cl
    
    def compute_time_score(self,triple):
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
    
    def compute_league_score(self,list_minor=None,list_major=None):
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
        # list_minor=[league for league in leagues if league not in major]
        # list_major=[league for league in leagues if league in major]
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
support=Manager(match_league_map,major,big_data,ls)
def processing(args):
    # support = Manager(args[0],args[1])
    k,j=args[0],args[1]
    # ls=ns.ls
    # big_data=ns.big_data
    # match_league_map=ns.match_league_map
    # major=ns.major
# for k in tqdm(range(len(ls)-1),desc="PROCESSING..."):
#   if i % 1e9 == 0:
#     mod = i % 1e9
#     os.mkdir(os.path.join(root,save_folder,"folder %.0f" % (mod+1)))
    a,b=support.cl[j],support.cl[k]
    info_a,info_b=support.cd[a],support.cd[b]

    comb_a,comb_b=set(info_a.keys()),set(info_b.keys())
#   for j in tqdm(range(k+1,len(ls)),desc=f"LOOP {k+1} . . ."):
# for b in ls:
    # i += 1
    # b = ls[k]
    
    # info_b=big_data[b]
    # comb_b=set(info_b.keys())
    intersec = comb_a.intersection(comb_b)
    if len(intersec)>0:
        # i += 1
        bet_count=0
        mil,mal,my_dict={},{},{}
        d = {}
        my_dict['C1']=str(a)
        my_dict['C2']=str(b)
        for comb in intersec:
        
            (match,bettype)=comb
            arr = np.concatenate((info_a[comb],info_b[comb]),axis=0)
            bet_count += arr.shape[0]
            l=support.mlm[match]['leagueid']
            if l in support.major:
                if l in mal:
                    mal[l] += 1
                # mal[l] +=1 if l in mal else mal[l]=1
                else:
                    mal[l]=1
            else:
                if l in mil:
                    mil[l] += 1
                # mil[l] +=1 if l in mil else mil[l]=1
                else:
                    mil[l]=1
    
            d[str(comb)]=arr[arr[:,2].argsort()]
        # i += 1
# if i > 1e6  or k == len(ls)-2:
        ts_result = pd.Series(d).apply(support.compute_time_score)
        
        ts_arr=ts_result.apply(lambda z : z[0]).values
        
        my_dict['TJSM']=len(ts_arr[ts_arr>0])

        #my_dict['eff_trans']=ts_result.apply(lambda z : z[1]).to_dict()
        
        my_dict['TJM']=len(intersec)
        my_dict['MS']=len(ts_arr[ts_arr>0]) / len(ts_arr)
        # print(f"MIL {mil.values()}",f"MAL {mal.values()}")
        my_dict['LS']=support.compute_league_score(list(mil.values()),list(mal.values()))
        
        # S['time_score']=S['time_score'].apply(lambda z: np.mean(np.array(z)[np.array(z) >0] if np.sum(z)>0 else 0))
        my_dict['TS']= np.mean(ts_arr[ts_arr>0]) if len(ts_arr[ts_arr>0]) > 0 else 0
        my_dict['BC']=bet_count
        my_dict['TJD'] = 1
        return my_dict
        # with open(os.path.join(output1a,f'{a}_{b}.json'), 'w') as g:
        # with open(os.path.join(root,save_folder,"folder %.0f" % (mod+1),f'{k}.pkl'), 'wb') as handle:  ,"folder %.0f" % (mod+1)
            # json.dump(my_dict, g)

    else:
        return ''
        # del d,DF,S,my_dict
        # del d,my_dict
        # gc.collect()
    # i = 0
    # d = {}

# def myfunc():
#     total_couples=int(binom(len(ls),2))
#     print(f"TOTAL COUPELS {total_couples}")
#     tasks=itertools.combinations([k for k in range(len(ls))],2)

#     pool = mp.Pool(processes=4)

#     for _ in tqdm(pool.imap_unordered(processing, itertools.islice(tasks,total_couples)), total=total_couples):
#         pass
if __name__ == "__main__":

    tqdm.pandas()
    i=0
    myls=[]
    start=time.time()
    for k in range(len(ls)-1):
        for j in range(k+1,len(ls)):
            i += 1
            myls.append((k,j))
            if i == 1e5:
                print("INSERT TIME %.0f seconds" % (time.time()-start))
                start=time.time()
                mysr=pd.Series(myls)
                mylady=mysr.progress_apply(processing)
                filtered=mylady[mylady != '']
                list_of_dict=filtered.to_list()
                jsonstr = json.dumps(list_of_dict)
                print(type(jsonstr))
                conn = MySQLConnection(user = 'darius.vn', password = '1qaz@Wsx3edc', host = '10.18.200.70', port = '3307', database = 'SPU_AIML')
                try:
                    if conn.is_connected():
                        cursor = conn.cursor()
                        cursor.callproc('SPU_AIML_InsertAssociationStats',[jsonstr,None])
                        conn.commit()
                        conn.close()
                        cursor.close()
                        
                except Exception as err:
                    print(err)
                print("APPLY TIME %.0f seconds" % (time.time()-start))
                del mysr,mylady
                i=0
                myls = []
                
    
    
        # break


# mkdir output1 output2 score_output trans_output match_output
# rm -r output1 output2 score_output trans_output match_output